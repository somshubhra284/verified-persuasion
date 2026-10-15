"""Score reason classifiers against reasons_testset.jsonl.

  python3 classify_eval.py                   # keyword baseline (no API, no deps)
  .venv/bin/python classify_eval.py --llm    # LLM classifier via any OpenAI-compatible API
  add --heldout to either to score the harder held-out set instead

LLM mode needs `openai` (installed in .venv) and an API key in .env or the environment. Defaults to Groq's free tier:
  GROQ_API_KEY=...   [MODEL=openai/gpt-oss-120b]   [BASE_URL=https://api.groq.com/openai/v1]
Backup provider: put OPENROUTER_API_KEY=... in .env and run with PROVIDER=openrouter in front of the command.
"""
import json, os, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile was shut down on Groq free tier, 16 Aug 2026
# ponytail: minimal .env reader (KEY=VALUE lines); real environment wins. python-dotenv if quoting is ever needed.
for line in (HERE / ".env").read_text().splitlines() if (HERE / ".env").exists() else []:
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
PROVIDERS = {"groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1"),
             "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1")}
PROVIDER = os.environ.get("PROVIDER", "groq")  # logged next to the model, so results from each host stay separable
BUCKETS = {f"B{i}" for i in range(8)}

# ponytail: substring keywords with first-match-wins ordering. Ceiling: no negation or context ("not young").
# Written by the same person who wrote the test set, so its score here is optimistic; check it on real answers.
KEYWORDS = {
    "B1": ["young", "healthy", "fit", "gym", "never been", "never needed", "hospital nahi", "rarely", "sick",
           "fever", "umar", "age group", "low risk", "smoke", "checkup", "chances", "health is"],
    "B2": ["company", "office", "corporate", "employer", "hr", "work", "firm", "mnc", "job", "group insurance", "psu"],
    "B3": ["reject", "scam", "never pay", "fine print", "terms", "trust", "chor", "agent", "lied", "cheat",
           "denied", "policy wording", "waiting period", "sub-limit", "cashless never", "pre-existing", "understand"],
    "B4": ["later", "baad mein", "after marriage", "when i'm", "next year", "not this year", "will do", "once i",
           "no hurry", "there's time", "settle", "when i actually", "kids", "i'll buy", "will buy", "think about it"],
    "B5": ["saving", "saved", "emergency fund", "expensive", "afford", "invest", "mutual fund", "sip", "paisa",
           "money", "premium", "waste", "down the drain", "nothing back", "self-insure", "chip in", "emi", "salary"],
    "B6": ["ayushman", "government", "govt", "modi card", "aiims", "esic", "cghs", "public hospital", "scheme"],
    "B7": ["dad", "papa", "father", "mom", "parents", "husband", "wife", "floater", "family policy", "family plan",
           "dependant", "whole family"],
}
PATTERNS = {b: [re.compile(r"\b" + re.escape(k)) for k in kws] for b, kws in KEYWORDS.items()}


def keyword_classify(text):
    t = text.lower()
    first = {}  # bucket -> earliest match position
    for b, pats in PATTERNS.items():
        hits = [m.start() for p in pats if (m := p.search(t))]
        if hits:
            first[b] = min(hits)
    ranked = sorted(first, key=first.get)
    return {"primary": ranked[0] if ranked else "B0", "secondary": ranked[1] if len(ranked) > 1 else None}


def make_client():
    from openai import OpenAI
    key_var, url = PROVIDERS[PROVIDER]
    return OpenAI(api_key=os.environ.get(key_var) or os.environ["OPENAI_API_KEY"],
                  base_url=os.environ.get("BASE_URL", url),
                  max_retries=4)  # SDK backs off on 429; free tier is ~8K tokens/min


def llm_classifier():
    client = make_client()
    model = os.environ.get("MODEL", DEFAULT_MODEL)
    system = (HERE / "prompts" / "classifier_prompt.md").read_text()

    def classify(text):
        r = client.chat.completions.create(model=model, temperature=0, response_format={"type": "json_object"}, messages=[
            {"role": "system", "content": system}, {"role": "user", "content": f"Answer: {text}"}])
        raw = r.choices[0].message.content.strip()
        try:
            return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except ValueError:
            return {"primary": "PARSE_ERROR", "secondary": None, "raw": raw}
    return classify


def evaluate(rows, classify):
    errors, per_bucket, sec_ok, sec_n = [], Counter(), 0, 0
    for r in rows:
        pred = classify(r["text"])
        per_bucket[(r["primary"], pred["primary"] == r["primary"])] += 1
        if pred["primary"] != r["primary"]:
            errors.append((r["id"], r["primary"], pred["primary"], r["text"]))
        if r["secondary"]:
            sec_n += 1
            sec_ok += pred.get("secondary") == r["secondary"]
    n = len(rows)
    print(f"Primary accuracy: {n - len(errors)}/{n} = {(n - len(errors)) / n:.0%}")
    print(f"Secondary accuracy on two-reason answers: {sec_ok}/{sec_n}")
    for b in sorted(BUCKETS):
        tot = per_bucket[(b, True)] + per_bucket[(b, False)]
        print(f"  {b}: {per_bucket[(b, True)]}/{tot}")
    false_b0 = sum(1 for _, gold, got, _ in errors if got == "B0" and gold != "B0")
    missed_b0 = sum(1 for _, gold, got, _ in errors if gold == "B0")
    print(f"Unneeded follow-ups (said B0, had a reason): {false_b0}")
    print(f"Missed follow-ups (guessed a bucket for a non-answer): {missed_b0}")
    print("Errors:")
    for e in errors:
        print(f"  {e[0]:6} gold {e[1]} got {e[2]}: {e[3]}")
    return len(errors)


if __name__ == "__main__":
    data = "reasons_heldout.jsonl" if "--heldout" in sys.argv else "reasons_testset.jsonl"
    rows = [json.loads(l) for l in (HERE / "data" / data).read_text().splitlines() if l.strip()]
    print("Test set:", data)
    # self-check: labels valid, ids unique, sanity cases for the baseline
    assert all(r["primary"] in BUCKETS and r["secondary"] in BUCKETS | {None} for r in rows)
    assert len({r["id"] for r in rows}) == len(rows)
    assert keyword_classify("I'm on my dad's floater")["primary"] == "B7"
    assert keyword_classify("pata nahi")["primary"] == "B0"
    assert keyword_classify("benefits are solid")["primary"] == "B0"  # 'fit' must not match inside 'benefits'

    use_llm = "--llm" in sys.argv
    print("Classifier:", f"LLM {os.environ.get('MODEL', DEFAULT_MODEL)} via {PROVIDER}" if use_llm else "keyword baseline")
    evaluate(rows, llm_classifier() if use_llm else keyword_classify)
