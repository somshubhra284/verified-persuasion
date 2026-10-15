"""Verified-persuasion conversation: classify the person's reason, argue only from that bucket's ledger claims.

  .venv/bin/python converse.py P01          # T0 -> conversation -> T1
  .venv/bin/python converse.py P01 --t2     # day-7 follow-up, appended to the same log
  .venv/bin/python converse.py --selfcheck  # offline asserts, no API

Every event goes to sessions/<participant>.jsonl with the claim IDs behind each reply.
"""
import json, os, sys, time
from classify_eval import HERE, DEFAULT_MODEL, make_client, llm_classifier

BUCKET_NAMES = {"B1": "young / healthy", "B2": "employer covers me", "B3": "claims rejected / scam / too complicated",
                "B4": "I'll buy later", "B5": "savings / too expensive", "B6": "government covers me",
                "B7": "on a family member's policy"}
REFUSAL = "I don't have a source for that, so I won't state it."
MAX_TURNS = 4
LEDGER = json.loads((HERE / "data" / "ledger.json").read_text())["claims"]


def allowed_claims(bucket):
    return [c for c in LEDGER if bucket in c["buckets"] and not c["status"].startswith("Hold")]


def check_reply(raw, allowed_ids):
    """Parse model output; return (reply, claim_ids, problem or None)."""
    try:
        out = json.loads(raw)
        reply, ids = out["reply"], list(out.get("claim_ids") or [])
        if out.get("refuse") and REFUSAL not in reply:  # exact wording guaranteed by code, not the model
            reply = f"{REFUSAL} {reply}".strip()
    except (ValueError, KeyError, TypeError):
        return None, [], "unparseable reply"
    bad = [i for i in ids if i not in allowed_ids]
    return reply, ids, (f"cited claims outside this bucket: {bad}" if bad else None)


def ask_score(prompt):
    while True:
        s = input(prompt).strip()
        if s.isdigit() and 0 <= int(s) <= 100:
            return int(s)
        print("Please type a whole number from 0 to 100.")


def logger(pid):
    path = HERE / "sessions" / f"{pid}.jsonl"
    path.parent.mkdir(exist_ok=True)

    def log(event, text=None, **extra):
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": pid, "event": event, "text": text, **extra}
        with path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return log


def say(text):
    print(f"\nBot: {text}\n")


def converse(pid):
    log, model = logger(pid), os.environ.get("MODEL", DEFAULT_MODEL)
    say("Hi! You're talking to a computer program, not a person. I'd like to understand one belief: "
        "\"I don't need a health insurance policy of my own.\" This is not financial advice.")
    log("t0", score=ask_score("How much do you agree, 0 (not at all) to 100 (completely)? "))
    reason = input("\nIn your own words, why do you feel you don't need your own policy?\nYou: ").strip()
    log("reason", reason)

    classify = llm_classifier()
    c = classify(reason)
    log("classify", reason, primary=c.get("primary"), secondary=c.get("secondary"), model=model)
    if c.get("primary") == "B0":
        say(c.get("follow_up") or "If you had to name one reason, what would it be?")
        reason = input("You: ").strip()
        log("reason", reason, follow_up=True)
        c = classify(reason)
        log("classify", reason, primary=c.get("primary"), secondary=c.get("secondary"), model=model)
    bucket = c.get("primary")
    if bucket not in BUCKET_NAMES:  # still B0 (or parse error): never guess a bucket
        say("Thanks, that's really helpful. That's all I needed.")
        log("end", reason="unclassified", bucket=bucket)
        return

    claims = allowed_claims(bucket)
    ids = {x["id"] for x in claims}
    system = ((HERE / "prompts" / "conversation_prompt.md").read_text()
              .replace("{reason}", reason).replace("{bucket}", bucket).replace("{bucket_name}", BUCKET_NAMES[bucket])
              .replace("{claims}", json.dumps([{k: x[k] for k in ("id", "claim", "figure", "source", "status", "care")}
                                               for x in claims], ensure_ascii=False, indent=1)))
    client, history = make_client(), [{"role": "user", "content": reason}]
    for turn in range(MAX_TURNS):
        msgs = [{"role": "system", "content": system}] + history
        for attempt in range(2):  # one retry with the problem spelled out, then refuse
            raw = client.chat.completions.create(model=model, temperature=0, response_format={"type": "json_object"},
                                                 messages=msgs).choices[0].message.content
            reply, cited, problem = check_reply(raw, ids)
            if not problem:
                break
            log("violation", raw, problem=problem, attempt=attempt)
            msgs = msgs + [{"role": "assistant", "content": raw},
                           {"role": "user", "content": f"(system) Invalid: {problem}. Use only the listed claims; reply as JSON."}]
        if problem:
            reply, cited = REFUSAL, []
        say(reply)
        log("assistant", reply, claim_ids=cited, bucket=bucket, model=model, turn=turn, fallback=bool(problem))
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
    assert check_reply('{"reply": "x", "claim_ids": ["C01"]}', b3)[2]  # C01 is B1-only
    assert check_reply("not json", b3)[2]
    assert check_reply('{"refuse": true, "reply": "Why?", "claim_ids": []}', b3)[0] == f"{REFUSAL} Why?"
    print("selfcheck ok")


if __name__ == "__main__":
    selfcheck()
    if len(sys.argv) > 1 and sys.argv[1] != "--selfcheck":
        (followup if "--t2" in sys.argv else converse)(sys.argv[1])
