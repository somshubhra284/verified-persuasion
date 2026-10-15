"""Verified-persuasion conversation: classify the person's reason, argue only from that bucket's ledger claims.

  .venv/bin/python converse.py P01          # system arm: consent, screening, T0 -> conversation -> T1
  .venv/bin/python converse.py P02 --brief  # baseline arm: same intake, then the fixed brief (data/fixed_brief.md) -> T1
  .venv/bin/python converse.py P01 --t2     # day-7 follow-up (either arm), appended to the same log
  .venv/bin/python converse.py --selfcheck  # offline asserts, no API

Every event goes to sessions/<participant>.jsonl with the claim IDs behind each reply.
"""
import hashlib, json, os, sys, time
from classify_eval import HERE, DEFAULT_MODEL, PROVIDER_TAG, make_client, llm_classifier

BUCKET_NAMES = {"B1": "young / healthy", "B2": "employer covers me", "B3": "claims rejected / scam / too complicated",
                "B4": "I'll buy later", "B5": "savings / too expensive", "B6": "government covers me",
                "B7": "on a family member's policy"}
REFUSAL = "I don't have a source for that, so I won't state it."
FOLLOW_UP = "What makes you ask about that?"  # added when a refusal would otherwise be the whole message
MAX_TURNS = 4
LEDGER = json.loads((HERE / "data" / "ledger.json").read_text())["claims"]


def allowed_claims(bucket):
    return [c for c in LEDGER if bucket in c["buckets"] and not c["status"].startswith("Hold")]


def usable_claims():
    """Since 16 Oct (Som): any non-Hold claim may answer a direct question; reason claims come from the buckets."""
    return [c for c in LEDGER if not c["status"].startswith("Hold")]


def reason_claims(buckets):
    """Claims for the person's reasons: the primary bucket's plus the secondary's, in ledger order."""
    return [c for c in usable_claims() if set(c["buckets"]) & {b for b in buckets if b}]

def check_reply(raw, allowed_ids):
    """Parse model output; return (reply, claim_ids, problem or None, premise or None, premise_claim or None)."""
    try:
        out = json.loads(raw)
        reply, ids = out["reply"], list(out.get("claim_ids") or [])
        premise = out.get("premise") or None
        # A factual premise the person stated that no allowed claim covers gets the refusal, enforced here
        # because the model left "costs double every five years" standing when it arrived as their reason.
        unsupported_premise = premise and out.get("premise_claim") not in allowed_ids
        refused = out.get("refuse") or unsupported_premise
        if not reply.strip() and not refused:
            return None, [], "empty reply", None, None
        if refused and REFUSAL not in reply:
            # never a dead end: the refusal always comes with something to answer
            reply = f"{REFUSAL} {reply.strip() or FOLLOW_UP}"
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, [], "unparseable reply", None, None
    bad = [i for i in ids if i not in allowed_ids]
    return reply, ids, (f"cited claims outside this bucket: {bad}" if bad else None), premise, out.get("premise_claim")


def ask_score(prompt):
    while True:
        s = input(prompt).strip()
        if s.isdigit() and 0 <= int(s) <= 100:
            return int(s)
        print("Please type a whole number from 0 to 100.")


def ask_yes(prompt):
    while True:
        s = input(prompt).strip().lower()
        if s in ("yes", "y", "no", "n"):
            return s.startswith("y")
        print("Please type yes or no.")


def file_sink(rec):
    path = HERE / "sessions" / f"{rec['pid']}.jsonl"
    path.parent.mkdir(exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def logger(pid, sink=file_sink):
    """sink(rec) stores one event; the web app passes its own (Supabase) sink. Same record shape everywhere."""
    def log(event, text=None, **extra):
        sink({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": pid, "event": event, "text": text, **extra})
    return log


def screen(age, own_policy, govt, t0):
    """Screening reasons (CLAUDE.md criteria); empty list = eligible."""
    return [why for failed, why in [(not 22 <= age <= 45, f"age {age}"), (own_policy, "has own policy"),
                                    (govt, "government scheme"), (t0 < 60, f"T0 {t0} < 60")] if failed]


def secondary_of(primary, secondary):
    return secondary if secondary in BUCKET_NAMES and secondary != primary else None


def system_prompt(bucket, reason, secondary=None):
    fields = ("id", "claim", "figure", "source", "status", "care")
    mine = reason_claims([bucket, secondary])
    other = [c for c in usable_claims() if c not in mine]
    dump = lambda cs: json.dumps([{k: x[k] for k in fields} for x in cs], ensure_ascii=False, indent=1)
    also = f" They also mentioned: {secondary} ({BUCKET_NAMES[secondary]})." if secondary else ""
    return ((HERE / "prompts" / "conversation_prompt.md").read_text()
            .replace("{reason}", reason).replace("{bucket}", bucket).replace("{bucket_name}", BUCKET_NAMES[bucket])
            .replace("{secondary_line}", also).replace("{claims}", dump(mine)).replace("{other_claims}", dump(other)))


def next_reply(client, model, system, history, bucket, turn, log, secondary=None):
    """One assistant turn: call the model, enforce the claim rules (one retry, then refuse), log it. Returns (reply, ids)."""
    ids = {x["id"] for x in usable_claims()}
    mine = {x["id"] for x in reason_claims([bucket, secondary])}
    msgs = [{"role": "system", "content": system}] + history
    for attempt in range(2):  # one retry with the problem spelled out, then refuse
        raw = client.chat.completions.create(model=model, temperature=0, response_format={"type": "json_object"},
                                             messages=msgs).choices[0].message.content
        reply, cited, problem, premise, premise_claim = check_reply(raw, ids)
        if not problem:
            break
        log("violation", raw, problem=problem, attempt=attempt)
        msgs = msgs + [{"role": "assistant", "content": raw},
                       {"role": "user", "content": f"(system) Invalid: {problem}. Use only the listed claims; reply as JSON."}]
    if problem:
        reply, cited, premise, premise_claim = REFUSAL, [], None, None
    log("assistant", reply, claim_ids=cited, bucket=bucket, buckets=[b for b in (bucket, secondary) if b],
        question_claims=[i for i in cited if i not in mine],  # used only because the person asked directly
        model=model, provider=PROVIDER_TAG, turn=turn, fallback=bool(problem),
        premise=premise, premise_claim=premise_claim, raw=raw)  # raw model output: shows whether code added the refusal
    return reply, cited


def say(text):
    print(f"\nBot: {text}\n")


def intake(log, arm):
    """Disclosure, consent, screening (CLAUDE.md criteria), T0 and reason. Returns the reason, or None if the session ends."""
    say("Hi! You're talking to a computer program, not a person. I'd like to understand one belief: "
        "\"I don't need a health insurance policy of my own.\" This is not financial advice. "
        "Your answers are saved without your name and used only for a study project. You can stop at any time (Ctrl-C).")
    if not ask_yes("Are you happy to take part? (yes/no) "):
        log("declined", arm=arm)
        say("No problem at all. Thank you for your time.")
        return None
    age = ask_score("How old are you? ")  # ponytail: reuses the 0-100 number prompt; age is in range
    own = ask_yes("Do you have a health insurance policy in your own name (not through work or family)? (yes/no) ")
    govt = ask_yes("Are you covered by CGHS, ESIC or PM-JAY (Ayushman Bharat)? (yes/no) ")
    t0 = ask_score("How much do you agree with \"I don't need a health insurance policy of my own\", "
                   "0 (not at all) to 100 (completely)? ")
    log("t0", score=t0, arm=arm, age=age)
    out = screen(age, own, govt, t0)
    if out:
        log("screened_out", arm=arm, reasons=out)
        say("Thank you, that's all I need from you today. You've been very helpful.")
        return None
    reason = input("\nIn your own words, why do you feel you don't need your own policy?\nYou: ").strip()
    log("reason", reason)
    return reason


def classify_reason(log, reason, model):
    """Classify, with one follow-up if B0. Returns (bucket, secondary or None, final reason text)."""
    classify = llm_classifier()
    c = classify(reason)
    log("classify", reason, primary=c.get("primary"), secondary=c.get("secondary"), model=model, provider=PROVIDER_TAG)
    if c.get("primary") == "B0":
        say(c.get("follow_up") or "If you had to name one reason, what would it be?")
        reason = input("You: ").strip()
        log("reason", reason, follow_up=True)
        c = classify(reason)
        log("classify", reason, primary=c.get("primary"), secondary=c.get("secondary"), model=model, provider=PROVIDER_TAG)
    return c.get("primary"), secondary_of(c.get("primary"), c.get("secondary")), reason


def converse(pid):
    log, model = logger(pid), os.environ.get("MODEL", DEFAULT_MODEL)
    reason = intake(log, "system")
    if reason is None:
        return
    bucket, secondary, reason = classify_reason(log, reason, model)
    if bucket not in BUCKET_NAMES:  # still B0 (or parse error): never guess a bucket
        say("Thanks, that's really helpful. That's all I needed.")
        log("end", reason="unclassified", bucket=bucket)
        return

    system = system_prompt(bucket, reason, secondary)
    client, history = make_client(), [{"role": "user", "content": reason}]
    for turn in range(MAX_TURNS):
        reply, cited = next_reply(client, model, system, history, bucket, turn, log, secondary)
        say(reply)
        history.append({"role": "assistant", "content": json.dumps({"reply": reply, "claim_ids": cited})})
        if turn == MAX_TURNS - 1:
            break
        user = input("You (type 'done' to finish): ").strip()
        if user.lower() == "done":
            break
        log("user", user)
        history.append({"role": "user", "content": user})

    say("Thank you for talking with me.")
    log("t1", score=ask_score("Now, how much do you agree: \"I don't need a health insurance policy of my own\"? (0-100) "))


def brief_arm(pid):
    log, model = logger(pid), os.environ.get("MODEL", DEFAULT_MODEL)
    reason = intake(log, "brief")
    if reason is None:
        return
    classify_reason(log, reason, model)  # bucket recorded for comparison by bucket; the brief is the same for all
    text = (HERE / "data" / "fixed_brief.md").read_text()
    print("\n" + "=" * 70 + "\n" + text + "\n" + "=" * 70)
    start = time.time()
    input("\nPress Enter when you've finished reading. ")
    log("brief_read", seconds=round(time.time() - start), brief_sha=hashlib.sha256(text.encode()).hexdigest()[:12])
    say("Thank you for reading.")
    log("t1", score=ask_score("Now, how much do you agree: \"I don't need a health insurance policy of my own\"? (0-100) "))


def followup(pid):
    log = logger(pid)
    log("t2", score=ask_score("Day 7: how much do you agree: \"I don't need a health insurance policy of my own\"? (0-100) "),
        looked_into_policy=input("Did you look into a policy this week? (yes/no) ").strip().lower())


def selfcheck():
    b3 = {c["id"] for c in allowed_claims("B3")}
    assert "C10" in b3, "C10 answers B3"
    assert all(not c["status"].startswith("Hold") for b in BUCKET_NAMES for c in allowed_claims(b))
    assert all("B2" in c["buckets"] for c in allowed_claims("B2"))
    assert check_reply('{"reply": "x", "claim_ids": ["C10"]}', b3)[2] is None
    usable = {c["id"] for c in usable_claims()}
    assert check_reply('{"reply": "x", "claim_ids": ["C25"]}', usable)[2]  # C25 is Hold: never usable
    assert check_reply('{"reply": "x", "claim_ids": ["C01"]}', usable)[2] is None  # any non-Hold claim may answer a question
    assert check_reply('{"refuse": true, "reply": "", "claim_ids": []}', b3)[0] == f"{REFUSAL} {FOLLOW_UP}"  # never bare
    assert check_reply('{"reply": "", "claim_ids": []}', b3)[2] == "empty reply"
    both = {c["id"] for c in reason_claims(["B2", "B5"])}
    assert {"C06", "C21"} <= both and "C10" not in both  # B2 + B5 claims, not B3
    p = system_prompt("B2", "x", "B5")
    assert "also mentioned: B5" in p and "{other_claims}" not in p and '"C10"' in p and '"C25"' not in p
    assert secondary_of("B2", "B2") is None and secondary_of("B2", None) is None and secondary_of("B2", "B5") == "B5"
    assert check_reply("not json", b3)[2]
    assert check_reply('{"refuse": true, "reply": "Why?", "claim_ids": []}', b3)[0] == f"{REFUSAL} Why?"
    # fix 1: an unsupported stated premise gets the refusal even when the model didn't set refuse
    r = check_reply('{"premise": "costs double every 5 years", "premise_claim": null, "reply": "Why?", "claim_ids": []}', b3)
    assert r[0] == f"{REFUSAL} Why?" and r[3] == "costs double every 5 years"
    assert check_reply('{"premise": "x", "premise_claim": "C01", "reply": "Why?", "claim_ids": []}', b3)[0].startswith(REFUSAL)
    # a premise a ledger claim speaks to (C10 contradicts "most rejected") is answered, not refused
    assert check_reply('{"premise": "most claims rejected", "premise_claim": "C10", "reply": "87% settled.", '
                       '"claim_ids": ["C10"]}', b3)[0] == "87% settled."
    assert check_reply('{"premise": null, "reply": "Hi.", "claim_ids": []}', b3)[0] == "Hi."
    assert screen(30, False, False, 80) == [] and screen(50, True, False, 40) == ["age 50", "has own policy", "T0 40 < 60"]
    assert "{claims}" not in system_prompt("B3", "x") and "{secondary_line}" not in system_prompt("B3", "x")
    assert "C25" in (HERE / "data" / "ledger.json").read_text() and "C25" not in (HERE / "data" / "fixed_brief.md").read_text()
    print("selfcheck ok")


if __name__ == "__main__":
    selfcheck()
    if len(sys.argv) > 1 and sys.argv[1] != "--selfcheck":
        (followup if "--t2" in sys.argv else brief_arm if "--brief" in sys.argv else converse)(sys.argv[1])
