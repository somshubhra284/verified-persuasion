"""Web version of the study: one live link for graders (try-out) and participants.

  .venv/bin/uvicorn app:app --reload        # local: events go to sessions/<pid>.jsonl, exactly like the CLI
  .venv/bin/python app.py --selfcheck       # offline: full flows with a fake model, no API

Hosting: the page (public/index.html) is a static Hugging Face Space; this API runs on Render
(`uvicorn app:app --host 0.0.0.0 --port $PORT`). On Render set SUPABASE_URL + SUPABASE_SECRET_KEY (events go to the
`events` table), SESSION_SECRET, OPENROUTER_API_KEY and ALLOWED_ORIGIN (the Space's https://...hf.space origin). Session state is rebuilt from each session's own event log, so nothing lives in memory
between requests. Event records have the same shape as converse.py's, so export_sessions.py + check_claims.py
+ analyze.py work unchanged.

IDs: participants who pass screening get P01, P02, ... (odd = system arm, even = brief arm, the CLAUDE.md rule);
declined / screened-out get S01, S02, ...; try-outs get demo-N (always the system arm, never counted, capped per
day); `?pilot=1` gives pilot-N (alternating arms, never counted).
"""
import hashlib, hmac, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

os.environ.setdefault("RATE_LIMIT_WAITS", "5,10,20,30")  # keeps one request under ~2 min, so the page doesn't look stuck
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import RateLimitError
import converse as cv
from classify_eval import HERE, DEFAULT_MODEL, PROVIDER_TAG, make_client, llm_classifier

MODEL = os.environ.get("MODEL", DEFAULT_MODEL)
DEMO_CAP = int(os.environ.get("DEMO_DAILY_CAP", "40"))
SECRET = os.environ.get("SESSION_SECRET") or ("" if os.environ.get("RENDER") else "dev-secret")
BRIEF = (HERE / "data" / "fixed_brief.md").read_text()


class FileStore:
    """Local: one JSONL file per session in a folder (sessions/ by default)."""
    def __init__(self, folder):
        self.dir = Path(folder)

    def append(self, rec):
        self.dir.mkdir(exist_ok=True)
        with (self.dir / f"{rec['pid']}.jsonl").open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def events(self, pid):
        f = self.dir / f"{pid}.jsonl"
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []

    def started(self, prefix, since=""):
        """Session ids with this prefix whose 'start' event is at or after `since`."""
        out = []
        for f in self.dir.glob("*.jsonl") if self.dir.exists() else []:
            first = json.loads(f.read_text().splitlines()[0])
            if first["event"] == "start" and first["pid"].startswith(prefix) and first["ts"] >= since:
                out.append(first["pid"])
        return out


class SupabaseStore:
    """Production: rows in the `events` table via Supabase's REST API (stdlib only)."""
    def __init__(self, url, key):
        self.base, self.key = url.rstrip("/") + "/rest/v1/events", key

    def _call(self, method, query="", body=None):
        req = urllib.request.Request(self.base + query, method=method, data=json.dumps(body).encode() if body else None,
                                     headers={"apikey": self.key, "Authorization": f"Bearer {self.key}",
                                              "Content-Type": "application/json", "Prefer": "return=minimal"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read() or "null")

    def append(self, rec):
        self._call("POST", body={"pid": rec["pid"], "ts": rec["ts"], "event": rec["event"], "data": rec})

    def events(self, pid):
        return [r["data"] for r in self._call("GET", f"?select=data&pid=eq.{urllib.parse.quote(pid)}&order=id.asc")]

    def started(self, prefix, since=""):
        q = f"?select=pid&event=eq.start&pid=like.{urllib.parse.quote(prefix)}*&ts=gte.{urllib.parse.quote(since)}"
        return [r["pid"] for r in self._call("GET", q)]


STORE = (SupabaseStore(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
         if os.environ.get("SUPABASE_URL") else FileStore(os.environ.get("SESSIONS_DIR", HERE / "sessions")))
app = FastAPI(title="Verified Persuasion")
# The page lives on Hugging Face Spaces and calls this API on Render: allow only that origin (comma-separated list).
ALLOWED = [o.strip() for o in os.environ.get("ALLOWED_ORIGIN", "").split(",") if o.strip()]
if ALLOWED:
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


def token(pid):
    if not SECRET:
        raise HTTPException(500, "SESSION_SECRET is not set")
    return hmac.new(SECRET.encode(), pid.encode(), hashlib.sha256).hexdigest()[:16]


def load(pid, tok):
    """Check the session token, return the session's events and a logger for it."""
    if not hmac.compare_digest(token(pid), tok or ""):
        raise HTTPException(403, "invalid session")
    events = STORE.events(pid)
    if not events:
        raise HTTPException(404, "unknown session")
    return events, cv.logger(pid, sink=STORE.append)


def first(events, name):
    return next((e for e in events if e["event"] == name), None)


def new_pid(mode, eligible):
    prefix = {"demo": "demo-", "pilot": "pilot-"}.get(mode) or ("P" if eligible else "S")
    n = len(STORE.started(prefix)) + 1  # ponytail: count-then-write race is fine at ~20 sessions; a DB sequence if it grows
    return (f"{prefix}{n:02d}" if prefix in ("P", "S") else f"{prefix}{n}"), n


def llm(fn):
    """Run one model step; a provider that stays rate-limited becomes a 'busy, try again' (the frontend retries)."""
    try:
        return fn()
    except RateLimitError:
        raise HTTPException(503, "The AI service is busy. Please wait a few seconds and press Try again.")


class Start(BaseModel):
    mode: str = "study"  # study | demo | pilot
    consent: bool
    age: int | None = None
    own_policy: bool | None = None
    govt: bool | None = None
    t0: int | None = None


class Turn(BaseModel):
    pid: str
    token: str
    text: str | None = None
    done: bool = False
    seconds: int | None = None
    score: int | None = None
    looked: str | None = None


@app.get("/")
def index():
    return FileResponse(HERE / "public" / "index.html")


@app.get("/api/health")
def health():
    """Called when the page loads, so a sleeping free Render instance starts waking while the person reads."""
    return {"ok": True}


@app.post("/api/start")
def start(s: Start):
    mode = s.mode if s.mode in ("study", "demo", "pilot") else "study"
    if mode == "demo" and len(STORE.started("demo-", since=time.strftime("%Y-%m-%d"))) >= DEMO_CAP:
        raise HTTPException(429, "The try-out limit for today has been reached. Please come back tomorrow.")
    if not s.consent:
        pid, _ = new_pid(mode, False)
        log = cv.logger(pid, sink=STORE.append)
        log("start", mode=mode)
        log("declined", arm=None)
        return {"status": "declined", "pid": pid}
    if None in (s.age, s.own_policy, s.govt, s.t0) or not (0 <= s.age <= 120 and 0 <= s.t0 <= 100):
        raise HTTPException(422, "Please answer every question.")
    out = cv.screen(s.age, s.own_policy, s.govt, s.t0)
    pid, n = new_pid(mode, not out)
    arm = "system" if mode == "demo" or n % 2 else "brief"
    log = cv.logger(pid, sink=STORE.append)
    log("start", mode=mode)
    if out and mode != "demo":  # try-outs are never screened out: graders get to see the system whoever they are
        log("t0", score=s.t0, arm=None, age=s.age)
        log("screened_out", arm=None, reasons=out)
        return {"status": "screened_out", "pid": pid}
    log("t0", score=s.t0, arm=arm, age=s.age)
    return {"status": "ok", "pid": pid, "arm": arm, "token": token(pid)}


@app.post("/api/reason")
def reason(t: Turn):
    """The person's 'why'. Classifies (one follow-up if B0), then returns the first reply or the brief."""
    events, log = load(t.pid, t.token)
    arm = first(events, "t0")["arm"]
    reasons = [e["text"] for e in events if e["event"] == "reason"]
    classes = [e for e in events if e["event"] == "classify"]
    if first(events, "end"):
        return {"end": "unclassified"}
    if len(classes) == len(reasons):  # otherwise this is a retry: the last reason is logged but not classified yet
        if not reasons:
            log("reason", t.text)
        elif classes[-1]["primary"] not in cv.BUCKET_NAMES and len(reasons) == 1:
            log("reason", t.text, follow_up=True)
        if len(reasons) < 2 and (not classes or classes[-1]["primary"] not in cv.BUCKET_NAMES):
            reasons.append(t.text)
    if len(classes) < len(reasons):
        c = llm(lambda: llm_classifier()(reasons[-1]))
        log("classify", reasons[-1], primary=c.get("primary"), secondary=c.get("secondary"), model=MODEL, provider=PROVIDER_TAG)
        classes.append({"primary": c.get("primary"), "follow_up": c.get("follow_up")})
    bucket = classes[-1]["primary"]
    if bucket not in cv.BUCKET_NAMES:  # never guess a bucket
        if len(reasons) == 1:
            return {"follow_up": classes[-1].get("follow_up") or "If you had to name one reason, what would it be?"}
        log("end", reason="unclassified", bucket=bucket)
        return {"end": "unclassified"}
    if arm == "brief":
        return {"brief": BRIEF}
    reply = next((e for e in events if e["event"] == "assistant"), None)
    if reply:
        return {"reply": reply["text"], "last": cv.MAX_TURNS == 1}
    text, _ = llm(lambda: cv.next_reply(make_client(), MODEL, cv.system_prompt(bucket, reasons[-1]),
                                        [{"role": "user", "content": reasons[-1]}], bucket, 0, log))
    return {"reply": text, "last": cv.MAX_TURNS == 1}


@app.post("/api/message")
def message(t: Turn):
    """One more turn in the system arm (or 'done'). History is rebuilt from the log, as converse.py builds it."""
    events, log = load(t.pid, t.token)
    reason_text = [e["text"] for e in events if e["event"] == "reason"][-1]
    bucket = [e for e in events if e["event"] == "classify"][-1]["primary"]
    history = [{"role": "user", "content": reason_text}]
    for e in events:
        if e["event"] == "assistant":
            history.append({"role": "assistant", "content": json.dumps({"reply": e["text"], "claim_ids": e["claim_ids"]})})
        elif e["event"] == "user":
            history.append({"role": "user", "content": e["text"]})
    turn = sum(e["event"] == "assistant" for e in events)
    if t.done or turn >= cv.MAX_TURNS or first(events, "t1"):
        return {"done": True}
    if events[-1]["event"] != "user":  # a retry after "busy" must not log the same message twice
        log("user", t.text)
        history.append({"role": "user", "content": t.text})
    text, _ = llm(lambda: cv.next_reply(make_client(), MODEL, cv.system_prompt(bucket, reason_text), history, bucket, turn, log))
    return {"reply": text, "last": turn == cv.MAX_TURNS - 1}


@app.post("/api/brief_done")
def brief_done(t: Turn):
    events, log = load(t.pid, t.token)
    if not first(events, "brief_read"):
        log("brief_read", seconds=t.seconds or 0, brief_sha=hashlib.sha256(BRIEF.encode()).hexdigest()[:12])
    return {"ok": True}


@app.post("/api/t1")
def t1(t: Turn):
    events, log = load(t.pid, t.token)
    if t.score is None or not 0 <= t.score <= 100:
        raise HTTPException(422, "Please give a number from 0 to 100.")
    if not first(events, "t1"):
        log("t1", score=t.score)
    return {"code": t.pid}


@app.post("/api/t2")
def t2(t: Turn):
    events, log = load(t.pid, t.token)
    if t.score is None or not 0 <= t.score <= 100 or t.looked not in ("yes", "no"):
        raise HTTPException(422, "Please answer both questions.")
    if not first(events, "t2"):
        log("t2", score=t.score, looked_into_policy=t.looked)
    return {"ok": True}


def selfcheck():
    import tempfile
    from types import SimpleNamespace as NS
    from fastapi.testclient import TestClient
    global STORE, make_client, llm_classifier
    calls = {"busy": 0}

    def create(**kw):
        if calls["busy"]:
            calls["busy"] -= 1
            import httpx
            raise RateLimitError("busy", response=httpx.Response(429, request=httpx.Request("POST", "http://x")), body=None)
        return NS(choices=[NS(message=NS(content=json.dumps({"reply": "About 87% were paid.", "claim_ids": ["C10"]})))])
    make_client = lambda: NS(chat=NS(completions=NS(create=create)))
    llm_classifier = lambda: (lambda text: {"primary": "B0" if "dunno" in text else "B3", "secondary": None,
                                            "follow_up": "What is your main reason?"})
    with tempfile.TemporaryDirectory() as d:
        STORE = FileStore(d)
        c = TestClient(app)
        ok = {"consent": True, "age": 30, "own_policy": False, "govt": False, "t0": 80}
        evs = lambda pid: [e["event"] for e in STORE.events(pid)]
        # P01: system arm, full conversation, with one "busy" retry that must not double-log the message
        s = c.post("/api/start", json=ok).json()
        assert (s["pid"], s["arm"]) == ("P01", "system"), s
        r = c.post("/api/reason", json={**s, "text": "claims get rejected"}).json()
        assert r["reply"] == "About 87% were paid." and not r["last"]
        calls["busy"] = 1
        assert c.post("/api/message", json={**s, "text": "really?"}).status_code == 503
        assert c.post("/api/message", json={**s, "text": "really?"}).json()["reply"]
        assert c.post("/api/message", json={**s, "done": True}).json() == {"done": True}
        assert c.post("/api/t1", json={**s, "score": 50}).json() == {"code": "P01"}
        assert evs("P01") == ["start", "t0", "reason", "classify", "assistant", "user", "assistant", "t1"], evs("P01")
        # P02: brief arm
        s2 = c.post("/api/start", json=ok).json()
        assert (s2["pid"], s2["arm"]) == ("P02", "brief")
        assert c.post("/api/reason", json={**s2, "text": "claims get rejected"}).json()["brief"] == BRIEF
        c.post("/api/brief_done", json={**s2, "seconds": 95})
        c.post("/api/t1", json={**s2, "score": 70})
        assert evs("P02") == ["start", "t0", "reason", "classify", "brief_read", "t1"]
        # screened out and declined take S numbers, never P numbers
        assert c.post("/api/start", json={**ok, "age": 50}).json() == {"status": "screened_out", "pid": "S01"}
        assert c.post("/api/start", json={"consent": False}).json() == {"status": "declined", "pid": "S02"}
        assert c.post("/api/start", json=ok).json()["pid"] == "P03"
        # try-out: never screened out, always the system arm; pilot alternates from pilot-1
        d1 = c.post("/api/start", json={**ok, "mode": "demo", "age": 60}).json()
        assert (d1["pid"], d1["arm"], d1["status"]) == ("demo-1", "system", "ok")
        assert c.post("/api/start", json={**ok, "mode": "pilot"}).json()["arm"] == "system"
        assert c.post("/api/start", json={**ok, "mode": "pilot"}).json()["arm"] == "brief"
        # B0 twice ends with no claims
        u = c.post("/api/start", json=ok).json()
        assert c.post("/api/reason", json={**u, "text": "dunno"}).json() == {"follow_up": "What is your main reason?"}
        assert c.post("/api/reason", json={**u, "text": "dunno really"}).json() == {"end": "unclassified"}
        # tokens: a wrong token is refused; the day-7 link works with the right one
        assert c.post("/api/t1", json={**s, "token": "x", "score": 1}).status_code == 403
        assert c.post("/api/t2", json={**s, "score": 40, "looked": "yes"}).json() == {"ok": True}
        assert evs("P01")[-1] == "t2"
        assert c.get("/").status_code == 200 and c.get("/api/health").json() == {"ok": True}
    print("selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
