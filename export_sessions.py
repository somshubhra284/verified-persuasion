"""Copy the live site's session events from Supabase into sessions/<pid>.jsonl, so the offline pipeline runs unchanged.

  .venv/bin/python export_sessions.py                  # all sessions -> sessions/*.jsonl
  .venv/bin/python export_sessions.py --t2-link P03    # print the day-7 link to send that participant
  .venv/bin/python export_sessions.py --contacts       # who left an optional contact, with their day-7 links
  .venv/bin/python export_sessions.py --selfcheck      # offline

Needs SUPABASE_URL, SUPABASE_SECRET_KEY, SESSION_SECRET (and APP_URL for links) in .env, the same values as on Render.
Then: check_claims.py sessions/P0N.jsonl -> check_claims.py --review sessions/P0N.check.jsonl -> analyze.py
"""
import json, os, sys, tempfile
from pathlib import Path
from classify_eval import HERE  # also loads .env


def write_sessions(rows, folder):
    """rows: [{'pid', 'data'}] in insert order. Writes one JSONL per pid; returns the pids written."""
    by_pid = {}
    for r in rows:
        by_pid.setdefault(r["pid"], []).append(r["data"])
    Path(folder).mkdir(exist_ok=True)
    for pid, events in by_pid.items():
        (Path(folder) / f"{pid}.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events))
    return sorted(by_pid)


def fetch_all():
    from app import SupabaseStore
    store, rows, page = SupabaseStore(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"]), [], 1000
    while True:  # PostgREST returns at most 1000 rows per request
        batch = store._call("GET", f"?select=pid,data&order=id.asc&limit={page}&offset={len(rows)}")
        rows += batch
        if len(batch) < page:
            return rows


def selfcheck():
    with tempfile.TemporaryDirectory() as d:
        rows = [{"pid": "P01", "data": {"event": "start"}}, {"pid": "S01", "data": {"event": "start"}},
                {"pid": "P01", "data": {"event": "t0"}}]
        assert write_sessions(rows, d) == ["P01", "S01"]
        assert [json.loads(l)["event"] for l in Path(d, "P01.jsonl").read_text().splitlines()] == ["start", "t0"]
    print("selfcheck ok")


if __name__ == "__main__":
    selfcheck()
    if "--contacts" in sys.argv:
        from app import SupabaseStore, token
        store = SupabaseStore(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
        base = os.environ.get("APP_URL", "https://<your-app>").rstrip("/")
        for r in store._call("GET", "?select=pid,contact,created_at&order=id.asc", table="contacts"):
            print(f"{r['pid']}\t{r['contact']}\t{r['created_at'][:10]}\t{base}/?t2={r['pid']}&k={token(r['pid'])}")
    elif "--t2-link" in sys.argv:
        from app import token
        pid = sys.argv[sys.argv.index("--t2-link") + 1]
        print(f"{os.environ.get('APP_URL', 'https://<your-app>.vercel.app').rstrip('/')}/?t2={pid}&k={token(pid)}")
    elif "--selfcheck" not in sys.argv:
        pids = write_sessions(fetch_all(), HERE / "sessions")
        print(f"exported {len(pids)} sessions to sessions/: {', '.join(pids)}")
