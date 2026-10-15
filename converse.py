"""Verified-persuasion conversation: classify the person's reason, argue only from that bucket's ledger claims.

  .venv/bin/python converse.py P01          # system arm: consent, screening, T0 -> conversation -> T1
  .venv/bin/python converse.py P02 --brief  # baseline arm: same intake, then the fixed brief (data/fixed_brief.md) -> T1
  .venv/bin/python converse.py P01 --t2     # day-7 follow-up (either arm), appended to the same log
  .venv/bin/python converse.py --selfcheck  # offline asserts, no API

Every event goes to sessions/<participant>.jsonl with the claim IDs behind each reply.
"""
import json, os, re, sys, time
from classify_eval import HERE, DEFAULT_MODEL, PROVIDER_TAG, make_client, llm_classifier

BUCKET_NAMES = {"B1": "young / healthy", "B2": "employer covers me", "B3": "claims rejected / scam / too complicated",
                "B4": "I'll buy later", "B5": "savings / too expensive", "B6": "government covers me",
                "B7": "on a family member's policy"}
REFUSAL = "I don't have a source for that, so I won't state it."
FOLLOW_UP = "What makes you ask about that?"  # added when a refusal would otherwise be the whole message
MAX_TURNS = 10  # hard cap only: the conversation ends on a "wrap" move (argument landed, or stalled); "done" ends it any time
STALL = 3  # this many non-positive stances in a row -> the code asks for a wrap-up
NOT_MOVING = {"neutral", "resisting", "disengaged"}
SCALE = 10  # belief score 0-10 (was 0-100 until 16 Oct)
MAX_CARDS = 6  # brief arm: at most this many relevant fact cards
LEDGER = json.loads((HERE / "data" / "ledger.json").read_text())["claims"]


def allowed_claims(bucket):
    return [c for c in LEDGER if bucket in c["buckets"] and not c["status"].startswith("Hold")]


def usable_claims():
    """Since 16 Oct (Som): any non-Hold claim may answer a direct question; reason claims come from the buckets."""
    return [c for c in LEDGER if not c["status"].startswith("Hold")]


def say_as(c):
    """How a claim must be attributed, built from its status and source so the model can't promote an insurer's page
    to 'IRDAI' or state an inference as a fact."""
    s, src = c["status"], c["source"]
    if s.startswith("Secondary") and "reported" not in src:
        return f"As reported by {src}, ..."
    if s.startswith("Inference"):
        return f"Based on {src}, this means ... (say it as reasoning, not as something the document states)"
    if s.startswith("Weak"):
        return f"According to {src} (a vendor or sponsored source), ..."
    return f"According to {src}, ..."


def reason_claims(buckets):
    """Claims for the person's reasons: the primary bucket's plus the secondary's, in ledger order."""
    return [c for c in usable_claims() if set(c["buckets"]) & {b for b in buckets if b}]

# feedback (16 Oct): "How do you feel about underwriting when you eventually switch?" - never ask about buying or migrating
BANNED_QUESTION = re.compile(r"\b(buy\w*|purchas\w*|migrat\w*|switch\w*|port(ing|ability)?|which (insurer|plan|policy)|sign up)\b", re.I)


def check_reply(raw, allowed_ids):
    """Parse model output; return (reply, claim_ids, problem or None, premise or None, premise_claim or None, meta).
    meta = {stance, move, new_point}: how the person is responding and what the reply does (logged; drives the ending)."""
    try:
        out = json.loads(raw)
        reply, ids = out["reply"], list(out.get("claim_ids") or [])
        reply = re.sub(r"[\x00-\x08\x0b-\x1f]", "", reply)  # safety net: some hosts emit stray control characters
        premise = out.get("premise") or None
        # A factual premise the person stated that no allowed claim covers gets the refusal, enforced here
        # because the model left "costs double every five years" standing when it arrived as their reason.
        unsupported_premise = premise and out.get("premise_claim") not in allowed_ids
        refused = out.get("refuse") or unsupported_premise
        if not reply.strip() and not refused:
            return None, [], "empty reply", None, None, {}
        question = (re.findall(r"[^.?!]*\?", reply) or [""])[-1]
        if BANNED_QUESTION.search(question):
            return None, [], f"the question asks about buying/migrating/insurers: {question.strip()!r}", None, None, {}
        if refused and REFUSAL not in reply:
            # the model sometimes writes its own refusal too ("I don't have a source for that specific rate, but ..."): drop it
            own = re.match(r"I don[’']t have a source for that[^.,]*[.,]\s*(?:but\s+)?", reply.strip())
            rest = reply.strip()[own.end():] if own else reply.strip()
            rest = rest[:1].upper() + rest[1:]
            # never a dead end: the refusal always comes with something to answer
            reply = f"{REFUSAL} {rest or FOLLOW_UP}"
    except (ValueError, KeyError, TypeError, AttributeError):
        return None, [], "unparseable reply", None, None, {}
    bad = [i for i in ids if i not in allowed_ids]
    meta = {k: out.get(k) for k in ("stance", "move", "new_point")}
    return reply, ids, (f"cited claims outside this bucket: {bad}" if bad else None), premise, out.get("premise_claim"), meta


def ask_score(prompt, hi=SCALE):
    while True:
        s = input(prompt).strip()
        if s.isdigit() and 0 <= int(s) <= hi:
            return int(s)
        print(f"Please type a whole number from 0 to {hi}.")


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
                                    (govt, "government scheme"), (t0 < 6, f"T0 {t0} < 6")] if failed]


def secondary_of(primary, secondary):
    return secondary if secondary in BUCKET_NAMES and secondary != primary else None


FIELDS = ("id", "claim", "figure", "source", "status", "care")


def dump_claims(cs):
    return json.dumps([{**{k: x[k] for k in FIELDS}, "say_as": say_as(x)} for x in cs], ensure_ascii=False, indent=1)


def make_plan(client, model, reason, bucket, secondary=None):
    """One call before the conversation: the person's crux, a 3-4 claim chain toward it, and the conclusion.
    Validated in code (usable IDs only, no repeats, <= 4); falls back to the bucket's first claims if it fails."""
    usable = {c["id"] for c in usable_claims()}
    buckets = ", ".join(f"{b} ({BUCKET_NAMES[b]})" for b in (bucket, secondary) if b)
    prompt = ((HERE / "prompts" / "plan_prompt.md").read_text().replace("{reason}", reason)
              .replace("{buckets}", buckets).replace("{claims}", dump_claims(usable_claims())))
    try:
        raw = client.chat.completions.create(model=model, temperature=0, response_format={"type": "json_object"},
                                             messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        out = json.loads(raw)
        chain, seen = [], set()
        for link in out.get("chain") or []:
            cid = (link or {}).get("claim_id")
            if cid in usable and cid not in seen and len(chain) < 4:
                chain.append({"claim_id": cid, "why": str(link.get("why") or "")}); seen.add(cid)
        plan = {"crux": str(out.get("crux") or ""), "chain": chain, "conclusion": str(out.get("conclusion") or "")}
    except (ValueError, KeyError, TypeError, AttributeError):
        plan = {"crux": "", "chain": [], "conclusion": ""}
    if not plan["chain"]:  # never converse without a plan
        plan["chain"] = [{"claim_id": c["id"], "why": ""} for c in reason_claims([bucket, secondary])[:3]]
        plan["fallback"] = True
    return plan


def plan_ids(plan):
    return [x["claim_id"] for x in (plan or {}).get("chain", [])]


def system_prompt(bucket, reason, secondary=None, plan=None):
    mine = reason_claims([bucket, secondary])
    mine += [c for c in usable_claims() if c["id"] in plan_ids(plan) and c not in mine]  # e.g. C05 for "buy later"
    other = [c for c in usable_claims() if c not in mine]
    also = f" They also mentioned: {secondary} ({BUCKET_NAMES[secondary]})." if secondary else ""
    plan_text = json.dumps(plan or {"crux": "", "chain": [], "conclusion": ""}, ensure_ascii=False, indent=1)
    return ((HERE / "prompts" / "conversation_prompt.md").read_text()
            .replace("{reason}", reason).replace("{bucket}", bucket).replace("{bucket_name}", BUCKET_NAMES[bucket])
            .replace("{secondary_line}", also).replace("{plan}", plan_text)
            .replace("{claims}", dump_claims(mine)).replace("{other_claims}", dump_claims(other)))


def should_wrap(stances, turn):
    """The code ends the argument when it has stalled or hits the cap. Stances are the model's reading of each of the
    person's messages; the first one reads their opening belief (resisting by definition), so it never counts."""
    later = stances[1:]
    return turn >= MAX_TURNS - 1 or (len(later) >= STALL and all(s in NOT_MOVING for s in later[-STALL:]))


def next_reply(client, model, system, history, bucket, turn, log, secondary=None, plan=None, wrap_now=False):
    """One assistant turn: call the model, enforce the claim rules (one retry, then refuse), log it.
    Returns (reply, ids, done, stance): done = this reply wrapped up (the model chose "wrap", or the code asked);
    stance = the model's reading of the person's last message (agrees/open/neutral/resisting/disengaged)."""
    ids = {x["id"] for x in usable_claims()}
    mine = {x["id"] for x in reason_claims([bucket, secondary])} | set(plan_ids(plan))
    msgs = [{"role": "system", "content": system}] + history
    if wrap_now:
        msgs.append({"role": "user", "content": "(system) Wrap up now: move = \"wrap\". In 1-2 sentences connect only what "
                     "you have already shown them, add no new fact, thank them, and ask no question."})
    for attempt in range(2):  # one retry with the problem spelled out, then refuse
        raw = client.chat.completions.create(model=model, temperature=0, response_format={"type": "json_object"},
                                             messages=msgs).choices[0].message.content
        reply, cited, problem, premise, premise_claim, meta = check_reply(raw, ids)
        if not problem:
            break
        log("violation", raw, problem=problem, attempt=attempt)
        msgs = msgs + [{"role": "assistant", "content": raw},
                       {"role": "user", "content": f"(system) Invalid: {problem}. Use only the listed claims; reply as JSON."}]
    if problem:
        reply, cited, premise, premise_claim, meta = REFUSAL, [], None, None, {}
    done = wrap_now or meta.get("move") == "wrap"
    log("assistant", reply, claim_ids=cited, bucket=bucket, buckets=[b for b in (bucket, secondary) if b],
        question_claims=[i for i in cited if i not in mine],  # used only because the person asked directly
        stance=meta.get("stance"), move=meta.get("move"), new_point=meta.get("new_point"), wrap_forced=wrap_now, done=done,
        model=model, provider=PROVIDER_TAG, turn=turn, fallback=bool(problem),
        premise=premise, premise_claim=premise_claim, raw=raw)  # raw model output: shows whether code added the refusal
    return reply, cited, done, meta.get("stance")


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
    age = ask_score("How old are you? ", hi=120)
    own = ask_yes("Do you have a health insurance policy in your own name (not through work or family)? (yes/no) ")
    govt = ask_yes("Are you covered by CGHS, ESIC or PM-JAY (Ayushman Bharat)? (yes/no) ")
    t0 = ask_score("How much do you agree with \"I don't need a health insurance policy of my own\", "
                   "0 (not at all) to 10 (completely)? ")
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

    client = make_client()
    plan = make_plan(client, model, reason, bucket, secondary)
    log("plan", plan["crux"], chain=plan["chain"], conclusion=plan["conclusion"], fallback=plan.get("fallback", False),
        plan_extra=[i for i in plan_ids(plan) if i not in {c["id"] for c in reason_claims([bucket, secondary])}])
    system, history, stances = system_prompt(bucket, reason, secondary, plan), [{"role": "user", "content": reason}], []
    for turn in range(MAX_TURNS):
        reply, cited, done, stance = next_reply(client, model, system, history, bucket, turn, log, secondary, plan,
                                                wrap_now=should_wrap(stances, turn))
        stances.append(stance)
        say(reply)
        history.append({"role": "assistant", "content": json.dumps({"reply": reply, "claim_ids": cited}, ensure_ascii=False)})
        if done:
            break
        user = input("You (type 'done' to finish): ").strip()
        if user.lower() == "done":
            break
        log("user", user)
        history.append({"role": "user", "content": user})

    say("Thank you for talking with me.")
    log("t1", score=ask_score("Now, how much do you agree: \"I don't need a health insurance policy of my own\"? (0-10) "))


def brief_cards(primary, secondary=None):
    """Brief arm (16 Oct): only the fixed brief's facts for the person's reason(s), tags stripped, primary bucket first.
    The wording is the brief's own (it names the source where needed); every bullet ends in exactly one [Cxx] tag."""
    bullets = re.findall(r"^- (.*?) \[(C\d\d)\]$", (HERE / "data" / "fixed_brief.md").read_text(), flags=re.M)
    by_id = {cid: text for text, cid in bullets}
    order = [c["id"] for b in (primary, secondary) if b for c in reason_claims([b])]
    ids = [cid for cid in dict.fromkeys(order) if cid in by_id][:MAX_CARDS]
    return [{"id": cid, "text": by_id[cid]} for cid in ids]


def brief_arm(pid):
    log, model = logger(pid), os.environ.get("MODEL", DEFAULT_MODEL)
    reason = intake(log, "brief")
    if reason is None:
        return
    bucket, secondary, _ = classify_reason(log, reason, model)
    if bucket not in BUCKET_NAMES:  # still B0: never guess a bucket (same as the system arm)
        say("Thanks, that's really helpful. That's all I needed.")
        log("end", reason="unclassified", bucket=bucket)
        return
    cards = brief_cards(bucket, secondary)
    start = time.time()
    for i, c in enumerate(cards, 1):
        print(f"\n[{i} of {len(cards)}] {c['text']}")
        input("Press Enter for the next one. " if i < len(cards) else "Press Enter when you've finished reading. ")
    log("brief_read", seconds=round(time.time() - start), cards=[c["id"] for c in cards])
    say("Thank you for reading.")
    log("t1", score=ask_score("Now, how much do you agree: \"I don't need a health insurance policy of my own\"? (0-10) "))


def followup(pid):
    log = logger(pid)
    log("t2", score=ask_score("Day 7: how much do you agree: \"I don't need a health insurance policy of my own\"? (0-10) "),
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
    # feedback 16 Oct: never ask about buying/migrating; harmless questions pass
    assert "buying/migrating" in check_reply('{"reply": "Fair. How do you feel about underwriting when you eventually switch?", "claim_ids": []}', b3)[2]
    assert check_reply('{"reply": "Fair. Do you trust insurers to pay?", "claim_ids": []}', b3)[2] is None
    assert check_reply('{"stance": "open", "move": "advance", "reply": "Ok.", "claim_ids": []}', b3)[5]["move"] == "advance"
    by = {c["id"]: c for c in LEDGER}
    assert say_as(by["C11"]).startswith("As reported by Royal Sundaram")  # an insurer's page, never "IRDAI states"
    assert say_as(by["C08"]).startswith("Based on IRDAI") and "reasoning" in say_as(by["C08"])  # Inference, as reasoning
    assert say_as(by["C10"]).startswith("According to IRDAI Annual Report")
    # ending: the opening stance never counts; 3 non-moving replies after it, or the cap, force a wrap
    assert not should_wrap(["resisting", "resisting", "neutral"], 2)
    assert should_wrap(["resisting", "resisting", "neutral", "disengaged"], 3)
    assert not should_wrap(["resisting", "open", "neutral", "resisting"], 3)
    assert should_wrap([], MAX_TURNS - 1)
    # plan validation: Hold, unknown and repeated IDs dropped; bad JSON falls back to the bucket's claims
    from types import SimpleNamespace as NS
    fake = lambda content: NS(chat=NS(completions=NS(create=lambda **kw: NS(choices=[NS(message=NS(content=content))]))))
    p = make_plan(fake(json.dumps({"crux": "x", "chain": [{"claim_id": i, "why": "w"} for i in
                                    ["C25", "C99", "C06", "C06", "C08", "C05", "C11", "C26"]], "conclusion": "y"})), "m", "r", "B2", "B4")
    assert plan_ids(p) == ["C06", "C08", "C05", "C11"] and not p.get("fallback")
    assert make_plan(fake("not json"), "m", "r", "B2")["fallback"] and plan_ids(make_plan(fake("{}"), "m", "r", "B2"))
    sp = system_prompt("B2", "r", "B4", p)
    assert "{plan}" not in sp and "As reported by Royal Sundaram" in sp and '"C05"' in sp.split("Other checked claims")[0]
    dup = check_reply('{"refuse": true, "reply": "I don\u2019t have a source for that specific rate, but costs rose 13%.", "claim_ids": []}', b3)
    assert dup[0] == f"{REFUSAL} Costs rose 13%.", dup[0]
    assert check_reply('{"reply": "2024\\u0018-25 data", "claim_ids": []}', b3)[0] == "2024-25 data"
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
    assert screen(30, False, False, 8) == [] and screen(50, True, False, 4) == ["age 50", "has own policy", "T0 4 < 6"]
    cards = brief_cards("B2", "B5")
    assert 1 <= len(cards) <= MAX_CARDS and all("[" not in c["text"] for c in cards)
    assert {c["id"] for c in cards} <= {c["id"] for c in reason_claims(["B2", "B5"])} and cards[0]["id"] in {"C06", "C07", "C08", "C09", "C26", "C27"}
    assert [c["id"] for c in brief_cards("B7")] == ["C32"]
    assert "{claims}" not in system_prompt("B3", "x") and "{secondary_line}" not in system_prompt("B3", "x")
    assert "C25" in (HERE / "data" / "ledger.json").read_text() and "C25" not in (HERE / "data" / "fixed_brief.md").read_text()
    print("selfcheck ok")


if __name__ == "__main__":
    selfcheck()
    if len(sys.argv) > 1 and sys.argv[1] != "--selfcheck":
        (followup if "--t2" in sys.argv else brief_arm if "--brief" in sys.argv else converse)(sys.argv[1])
