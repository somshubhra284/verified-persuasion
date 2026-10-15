"""Drive simulated personas through the LIVE platform (Render API -> Cerebras -> Supabase), one turn at a time.

  .venv/bin/python sim.py start SIM01 system 8 "My company already gives me ..." [--age 29]
  .venv/bin/python sim.py say SIM01 "persona reply"
  .venv/bin/python sim.py done SIM01        # end the chat (like "I'm done")
  .venv/bin/python sim.py t1 SIM01 6
  .venv/bin/python sim.py show SIM01        # the session as logged

Sessions run in `sim` mode (ids sim-N, arm chosen, never counted by analyze.py). Tokens are kept in the scratchpad
(SIM_STATE), never in the repo. Needs the .env Supabase keys to read the logged details.
"""
import json, os, sys, urllib.request
from pathlib import Path
from app import SupabaseStore  # noqa: also loads .env via classify_eval

API = os.environ.get("SIM_API", "https://verified-persuasion-f0vv.onrender.com")
STATE = Path(os.environ.get("SIM_STATE", "/private/tmp/claude-501/-Users-SOMSHUBHRA-Desktop-100x-engineers-Cohort-End-Capstone-Project-verified-persuasion/729a8a95-09db-43ce-b5e7-d696f036aad0/scratchpad/sim-state.json"))
REF = "I don't have a source for that, so I won't state it."


def post(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    import ssl, certifi
    with urllib.request.urlopen(req, timeout=300, context=ssl.create_default_context(cafile=certifi.where())) as r:
        return json.loads(r.read())


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def events(pid):
    import time
    for attempt in range(4):  # Supabase occasionally answers HTTP 555 on reads (seen twice on 16 Oct); retry
        try:
            return SupabaseStore(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"]).events(pid)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def show_last(pid):
    ev = events(pid)
    plan = next((e for e in ev if e["event"] == "plan"), None)
    a = [e for e in ev if e["event"] == "assistant"]
    if plan and len(a) == 1:
        print(f"[plan] crux: {plan['text']}\n       chain: {[x['claim_id'] for x in plan['chain']]}  extra: {plan.get('plan_extra')}")
    if a:
        e = a[-1]
        print(f"[bot #{len(a)}] move={e.get('move')} stance={e.get('stance')} claims={e['claim_ids']} "
              f"question_claims={e.get('question_claims')} premise={e.get('premise')!r} "
              f"refusal={'yes' if e['text'].startswith(REF) else 'no'} done={e.get('done')} forced_wrap={e.get('wrap_forced')}")
        print(f"BOT: {e['text']}")


if __name__ == "__main__":
    cmd, sim = sys.argv[1], sys.argv[2]
    st = state()
    if cmd == "start":
        arm, t0, text = sys.argv[3], int(sys.argv[4]), sys.argv[5]
        age = int(sys.argv[sys.argv.index("--age") + 1]) if "--age" in sys.argv else 28
        s = post("/api/start", {"mode": "sim", "arm": arm, "label": sim, "consent": True, "age": age,
                                "own_policy": False, "govt": False, "t0": t0})
        print(f"[start] {sim} -> {s.get('pid')} status={s['status']} arm={s.get('arm')}")
        st[sim] = {"pid": s["pid"], "token": s.get("token")}
        STATE.write_text(json.dumps(st))
        if s["status"] != "ok":
            print("(session ended at screening: no reason asked)")
            sys.exit()
        r = post("/api/reason", {"pid": s["pid"], "token": s["token"], "text": text})
        if r.get("cards"):
            print(f"[brochure] {len(r['cards'])} cards, {sum(len(c['facts']) for c in r['cards'])} facts: "
                  + " | ".join(c["title"] for c in r["cards"]))
            post("/api/brief_done", {"pid": s["pid"], "token": s["token"], "seconds": 0})
        elif r.get("follow_up"):
            print(f"[follow-up question] {r['follow_up']}")
        elif r.get("end"):
            print("[ended] unclassified")
        else:
            show_last(s["pid"])
        print(f"[classify] {[(e['primary'], e.get('secondary')) for e in events(s['pid']) if e['event'] == 'classify']}")
    elif cmd == "say":
        s = st[sim]
        ev = events(s["pid"])
        if any(e["event"] == "classify" and e["primary"] == "B0" for e in ev) and not any(e["event"] == "assistant" for e in ev):
            r = post("/api/reason", {"pid": s["pid"], "token": s["token"], "text": sys.argv[3]})  # B0 follow-up answer
            print(f"[classify] {[(e['primary'], e.get('secondary')) for e in events(s['pid']) if e['event'] == 'classify']}")
            if r.get("end"):
                print("[ended] still unclassified: no claims made")
                sys.exit()
        else:
            r = post("/api/message", {"pid": s["pid"], "token": s["token"], "text": sys.argv[3]})
        if r.get("done"):
            print("[conversation already finished]")
        else:
            show_last(s["pid"])
            if r.get("last"):
                print("[the bot wrapped up: conversation over]")
    elif cmd == "done":
        s = st[sim]
        print(post("/api/message", {"pid": s["pid"], "token": s["token"], "done": True}))
    elif cmd == "t1":
        s = st[sim]
        print(post("/api/t1", {"pid": s["pid"], "token": s["token"], "score": int(sys.argv[3])}))
    elif cmd == "show":
        for e in events(st[sim]["pid"]):
            print(e["event"], {k: v for k, v in e.items() if k not in ("ts", "pid", "event", "raw")})
