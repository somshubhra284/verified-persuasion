"""Post-hoc checker: count unsupported claims in logged conversation replies.

  .venv/bin/python check_claims.py sessions/P01.jsonl [...]   # writes sessions/P01.check.jsonl
  .venv/bin/python check_claims.py --gold                     # score the checker on data/checker_gold.jsonl
  .venv/bin/python check_claims.py --selfcheck                # offline asserts, no API
  .venv/bin/python check_claims.py --review sessions/P01.check.jsonl   # Som hand-labels every sentence (offline)

Since 16 Oct the checker is a first pass: the hand labels from --review are the unsupported-claims metric,
and the summary records how often the checker agreed with them.

Layer 1 (deterministic): every number in a reply must appear in a cited claim's claim/figure/source.
Layer 2 (LLM judge): every sentence is non-factual / supported / uncited / unsupported against the claims.
A sentence takes the worse of the two layers. Unsupported claims = uncited + unsupported.
"""
import json, os, re, sys
from pathlib import Path
from classify_eval import HERE, DEFAULT_MODEL, PROVIDER_TAG, make_client
from converse import LEDGER, usable_claims

BY_ID = {c["id"]: c for c in LEDGER}
RANK = {"non-factual": 0, "supported": 0, "uncited": 1, "unsupported": 2, "unjudged": 2}
FLAGS = {"uncited", "unsupported", "unjudged"}
WORDS = dict(zip("zero one two three four five six seven eight nine ten".split(), map(str, range(11))))
W = "|".join(WORDS)


def numbers(text):
    """Normalized numbers in text: '63,71,620' -> '6371620', '86.880' -> '86.88', 'four in ten' -> {'4', '10'}."""
    t = text.lower()
    out = set()
    for x in re.findall(r"\d[\d,]*(?:\.\d+)?", t):
        x = x.replace(",", "")
        out.add(x.rstrip("0").rstrip(".") if "." in x else x)
    # ponytail: number words only as ratios ("four in ten") or "zero"; bare "one"/"two" are too common to flag
    for a, b in re.findall(rf"\b({W})\s+in\s+({W})\b", t):
        out |= {WORDS[a], WORDS[b]}
    if re.search(r"\bzero\b", t):
        out.add("0")
    return out


def claim_numbers(c):
    return numbers(" ".join([c["claim"], c["figure"] or "", c["source"]]))


def in_pool(n, pool):
    """n is in pool exactly, or is a pool number rounded to n's precision (86.88 -> 86.9 or 87)."""
    if n in pool:
        return True
    d = len(n.split(".")[1]) if "." in n else 0
    return any("." in x and len(x.split(".")[1]) > d and round(float(x), d) == float(n) for x in pool)


def check_numbers(sentence, cited_ids, user_nums):
    """Layer 1: [(number, 'uncited'|'unsupported', claim_id or None)] for numbers no cited claim contains."""
    cited = set().union(*(claim_numbers(BY_ID[i]) for i in cited_ids if i in BY_ID))
    flags = []
    for n in sorted(x for x in numbers(sentence) if not in_pool(x, cited) and x not in user_nums):
        other = next((c["id"] for c in usable_claims() if in_pool(n, claim_numbers(c))), None)
        flags.append((n, "uncited" if other else "unsupported", other))
    return flags


def split_sentences(reply):
    return [s for s in re.split(r"(?<=[.?!])\s+", reply.strip()) if s]


def judge(sentences, cited_ids, client, model, user_text=""):
    """Layer 2: one LLM call per reply; returns {n: label dict}. user_text = what the person said so far (echo fix)."""
    fields = ("id", "status", "claim", "figure", "source")
    cited = [{k: BY_ID[i][k] for k in fields} for i in cited_ids if i in BY_ID]
    # since 16 Oct any non-Hold claim may answer a direct question, so the checker judges against the whole usable ledger
    others = [{k: c[k] for k in fields} for c in usable_claims() if c["id"] not in cited_ids]
    user = (f"CITED claims:\n{json.dumps(cited, ensure_ascii=False)}\n\nOTHER claims:\n{json.dumps(others, ensure_ascii=False)}"
            f"\n\nWhat the PERSON said so far:\n{user_text.strip() or '(nothing)'}"
            "\n\nSentences:\n" + "\n".join(f"{n}. {s}" for n, s in enumerate(sentences, 1)))
    r = client.chat.completions.create(model=model, temperature=0, response_format={"type": "json_object"}, messages=[
        {"role": "system", "content": (HERE / "prompts" / "checker_prompt.md").read_text()},
        {"role": "user", "content": user}])
    try:
        return {s["n"]: s for s in json.loads(r.choices[0].message.content)["sentences"]}
    except (ValueError, KeyError, TypeError):
        return {}


def check_reply(reply, cited_ids, user_text, client, model):
    sentences = split_sentences(reply)
    labels, user_nums = judge(sentences, cited_ids, client, model, user_text), numbers(user_text)
    rows = []
    for n, s in enumerate(sentences, 1):
        j = labels.get(n, {"label": "unjudged", "claim_id": None, "why": "judge returned no label"})
        label = j["label"] if j["label"] in RANK else "unjudged"
        num_flags = check_numbers(s, cited_ids, user_nums)
        worst_num = max((f[1] for f in num_flags), key=RANK.get, default="supported")
        rows.append({"n": n, "sentence": s, "label": max(label, worst_num, key=RANK.get), "judge": label,
                     "claim_id": j.get("claim_id"), "why": j.get("why"), "num_flags": num_flags})
    return rows


def check_session(path, client, model):
    out_rows, user_text, totals = [], "", {k: 0 for k in ("supported", "uncited", "unsupported", "unjudged")}
    for line in Path(path).read_text().splitlines():
        e = json.loads(line)
        if e["event"] in ("reason", "user"):
            user_text += " " + (e["text"] or "")
        if e["event"] != "assistant":
            continue
        for r in check_reply(e["text"], e.get("claim_ids") or [], user_text, client, model):
            r.update(turn=e["turn"], cited=e.get("claim_ids"))
            out_rows.append(r)
            totals[r["label"]] = totals.get(r["label"], 0) + 1
            if r["label"] in FLAGS:
                print(f"  turn {r['turn']} [{r['label']}] {r['sentence']}\n      judge: {r['judge']} {r['claim_id'] or ''} "
                      f"({r['why']}); numbers: {r['num_flags'] or 'ok'}")
    factual = sum(v for k, v in totals.items() if k != "non-factual")
    summary = {"session": Path(path).stem, "model": model, "provider": PROVIDER_TAG, "factual_sentences": factual, **totals,
               "unsupported_claims": totals["uncited"] + totals["unsupported"] + totals["unjudged"]}
    with open(Path(path).with_suffix(".check.jsonl"), "w") as f:
        for r in out_rows + [{"summary": summary}]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(summary)
    return summary


HAND_KEYS = {"n": "non-factual", "s": "supported", "c": "uncited", "u": "unsupported"}


def review(path, ask=input):
    """Hand review: every sentence gets a human label (Enter keeps the checker's). Adds 'hand' per row and hand totals."""
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    body, summary = rows[:-1], rows[-1]["summary"]
    for r in body:
        while True:
            a = ask(f"\nturn {r['turn']}  cited {r['cited']}\n  {r['sentence']}\n  checker: {r['label']} ({r.get('why')})"
                    "\n  Enter = keep, or n(on-factual) / s(upported) / c (uncited) / u(nsupported): ").strip().lower()
            if a in HAND_KEYS or (a == "" and r["label"] in HAND_KEYS.values()):  # an 'unjudged' row needs a letter
                r["hand"] = HAND_KEYS.get(a, r["label"])
                break
    flagged = lambda r: r["hand"] in ("uncited", "unsupported")
    summary.update(hand_factual=sum(r["hand"] != "non-factual" for r in body), hand_unsupported=sum(map(flagged, body)),
                   checker_agreement=f"{sum((r['label'] in FLAGS) == flagged(r) for r in body)}/{len(body)}")
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in body + [{"summary": summary}]))
    return summary


def score_gold(client, model):
    rows = [json.loads(l) for l in (HERE / "data" / "checker_gold.jsonl").read_text().splitlines() if l.strip()]
    missed, false_flags, exact = [], [], 0
    for g in rows:
        got = max((r["label"] for r in check_reply(g["sentence"], g["cited_ids"], g.get("user_text", ""),
                                                   client, model)), key=RANK.get)
        exact += got == g["label"] or (RANK[got] == RANK[g["label"]] == 0)
        if g["label"] in FLAGS and got not in FLAGS:
            missed.append((g["id"], g["label"], got, g["sentence"]))
        elif g["label"] not in FLAGS and got in FLAGS:
            false_flags.append((g["id"], g["label"], got, g["sentence"]))
    n_flag = sum(g["label"] in FLAGS for g in rows)
    print(f"Gold: {len(rows)} sentences, {n_flag} should be flagged ({model} via {PROVIDER_TAG})")
    print(f"Recall on flagged: {n_flag - len(missed)}/{n_flag}   False flags: {len(false_flags)}   "
          f"Label agreement: {exact}/{len(rows)}")
    for kind, lst in (("MISSED", missed), ("FALSE FLAG", false_flags)):
        for i, gold, got, s in lst:
            print(f"  {kind} {i} gold {gold} got {got}: {s}")
    print("PASS" if not missed and len(false_flags) <= 2 else "FAIL", "(bar: recall 100%, <= 2 false flags)")


def selfcheck():
    assert numbers("about four in ten complaints") == {"4", "10"}
    assert numbers("₹24,000 (≈$248)") == {"24000", "248"}
    assert numbers("86.88% of 63,71,620") == {"86.88", "6371620"}
    assert numbers("one major insurer") == set()
    assert check_numbers("87% were settled and 8% rejected.", ["C10"], set()) == []
    assert [f[0] for f in check_numbers("12% of claims were rejected.", ["C10"], set())] == ["12"]  # flagged (C24 has a 12 elsewhere)
    assert check_numbers("Waiting periods start from zero.", ["C06"], set()) == [("0", "uncited", "C08")]
    assert check_numbers("Your 5 lakh cover stays with the employer.", ["C06"], numbers("my 5 lakh cover")) == []
    assert check_numbers("Insurers met the 1-hour target for 86.9% of requests.", ["C14"], set()) == []  # rounds 86.88
    assert check_numbers("Insurers met the 1-hour target for 87% of requests.", ["C14"], set()) == []
    assert [f[0] for f in check_numbers("About 52% of health complaints went to the policyholder.", ["C30"], set())] == ["52"]  # all-lines 52% removed from C30 (fix 2)
    from types import SimpleNamespace as NS
    from classify_eval import pin
    fake = lambda host, model: (lambda **kw: NS(model_extra={"provider": host}, model=model))
    assert pin(fake("Groq", "m"), "Groq")(model="m").model == "m"
    for bad in (fake("Novita", "m"), fake("Groq", "other")):
        try:
            pin(bad, "Groq")(model="m"); raise AssertionError("pin let a wrong host/model through")
        except RuntimeError:
            pass
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = Path(d, "x.check.jsonl")
        rows = [{"turn": 0, "cited": ["C10"], "sentence": s, "label": l} for s, l in
                [("87% paid.", "supported"), ("So most are approved.", "supported"), ("Hi?", "non-factual"), ("x", "unjudged")]]
        f.write_text("".join(json.dumps(r) + "\n" for r in rows + [{"summary": {"session": "x"}}]))
        answers = iter(["", "u", "", "", "s"])  # the blank for the unjudged row is refused, then 's'
        s = review(f, ask=lambda _: next(answers))
        assert s["hand_unsupported"] == 1 and s["hand_factual"] == 3 and s["checker_agreement"] == "2/4", s
    print("selfcheck ok")


if __name__ == "__main__":
    selfcheck()
    args = [a for a in sys.argv[1:] if a != "--selfcheck"]
    if args[:1] == ["--review"]:
        for p in args[1:]:
            print(review(p))
    elif args:
        client, model = make_client(), os.environ.get("MODEL", DEFAULT_MODEL)
        if args == ["--gold"]:
            score_gold(client, model)
        else:
            for p in args:
                print(f"== {p}")
                check_session(p, client, model)
