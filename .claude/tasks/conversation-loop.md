# Plan: Conversation loop MVP (CLAUDE.md next steps 1–2)

Saved to `.claude/tasks/conversation-loop.md` once approved (plan mode only lets me write here first).

## Context
Done so far: belief spec, ledger v1 (33 claims), fixed brief, classifier test sets, keyword baseline (71% held-out). Step 1, the LLM classifier run, is blocked on a Groq key. Step 2 is the core of the capstone: a chat that classifies the person's reason, argues only from that bucket's ledger claims, names sources, refuses anything off-ledger, and logs every turn with claim IDs. Steps 3 to 5 (checker, reversal runs, participants) all depend on these logs, so the log format is the main design decision here.

MVP means one new script, one new prompt file and no framework. The operator (Som) runs it in a terminal next to the participant, or the participant types into it.

## Decisions (defaults; change any of them at review)
- **Claims in play:** primary bucket only, since the rule says "the person's bucket". Status `Hold` is never sent to the model. Statuses are matched by prefix, because the ledger has variants like `Primary (abstract)` and `Primary (chart undated)`.
- **B0 after one follow-up:** if the person is still B0, the system doesn't guess. It logs `bucket: B0`, says thanks and ends. The session is excluded from analysis.
- **Length:** at most 4 system turns, or fewer if the person types `done`. Then T1 is asked.
- **T2 (day 7):** `--t2` mode asks the score and "Did you look into a policy this week?", and appends both to the same log.
- **Privacy:** `sessions/` is gitignored, because it holds real participants' words.
- **Key loading:** a 3-line stdlib `.env` reader added to `classify_eval.py` and reused, so nobody has to remember `source .env`. No python-dotenv.
- **Model:** whatever the Groq research confirms is current (see Research). The model is set by the `MODEL` env var, as it already is.

## Tasks
(Order: 1 → 0 → 2…6. Task 0 needs Task 1's model fix.)
0. **Run the classifier eval** (needs your key in `.env`): `.venv/bin/python classify_eval.py --llm --heldout`. Record the result in CLAUDE.md Status, against the pre-set bar of ≥90% and ≤2 wrong buckets. If it fails, stop and plan prompt fixes separately. Step 2 still works with a weaker classifier, but the result changes what we claim.
1. **`classify_eval.py`** (do this before Task 0): add a `.env` loader at the top (only sets keys not already in the environment). Change the default `MODEL` to `openai/gpt-oss-120b`. Pass `response_format={"type":"json_object"}`. Retry once on 429. Fix the docstring: `python` → `python3`/`.venv`.
2. **`prompts/conversation_prompt.md`:** the system prompt. It holds the hard rules from CLAUDE.md (status → phrasing table, the refusal sentence, no premiums/insurers/tax beyond C20/medical/personal risk, a not-financial-advice line once, argue against the belief and not for a purchase). Its `{claims}` slot gets the allowed claims as JSON (id, claim, figure, source, status, care). The model must reply as JSON `{"reply": str, "claim_ids": [..]}`.
3. **`converse.py <participant_id>`**, about 100 lines:
   - intro (machine disclosure; consent was already taken offline) → ask T0 score (0–100, validated) and their reason, verbatim
   - classify with `llm_classifier()` from `classify_eval.py` (reused, not copied); one follow-up if B0
   - `allowed = [c for c in ledger if bucket in c.buckets and not c.status.startswith("Hold")]`
   - loop: send the history and the allowed claims → parse the JSON → **guard**: if any cited ID isn't in `allowed`, or the JSON doesn't parse, retry once, then log it as `violation` and show the refusal line instead
   - log every event as one JSONL line to `sessions/<pid>.jsonl`: `{ts, pid, event: t0|reason|classify|user|assistant|t1|t2, text, bucket, claim_ids, model, flags}`
   - end: ask T1 score
   - `--t2`: append the T2 score and the yes/no answer
   - self-check asserts in `__main__`, in the style of `classify_eval.py`: Hold excluded, bucket filter correct, the guard rejects a foreign ID
4. **`.gitignore`:** add `sessions/`.
5. **Dry run** as a fake participant for B2, B3 (try a question off the ledger) and B0. Read the logs by hand.
6. **Update CLAUDE.md Status** and this task file with a log of the changes.

## Not in this plan (later steps)
Post-hoc checker (step 3), reversal runs R1/R2 (step 4; these run through this same script, using the claim text as the "reason"), any web UI.

## Risks
- B7 has only 1 claim and B6 has 3, so those conversations will be thin. That's honest; it gets logged and noted in the write-up.
- An LLM can paraphrase a figure wrongly even when it cites the right ID. The guard can't catch that; the step 3 checker will.

## Research (Groq docs, 15 Oct 2026)
- **`llama-3.3-70b-versatile` was shut down on 16 Aug 2026** for free and developer tiers. The current default in `classify_eval.py` would fail. The replacement is **`openai/gpt-oss-120b`**, which becomes the new default in both scripts. Record the model change in CLAUDE.md next to the classifier result, because the pass bar was set before the model was chosen.
- Limits (Developer-plan base; Free may be lower): 30 requests/min, 1,000 requests/day, 8K tokens/min, 200K tokens/day. The 48-row eval is fine. A conversation is about 6 calls, but each call carries about 3K tokens of claims and history, so the 8K tokens/min limit allows roughly 2 calls a minute. The scripts sleep and retry once on a 429.
- `response_format={"type":"json_object"}` is supported. Use it for the classifier and the conversation, which removes most parse errors. The prompt must still say "JSON".
- Sources: console.groq.com/docs/deprecations, /rate-limits, /structured-outputs

## Verification
- `.venv/bin/python converse.py --selfcheck` (or just running it): the asserts pass.
- Dry runs from Task 5 give `sessions/test-*.jsonl` files where every assistant line has `claim_ids` ⊆ that bucket's allowed IDs, with no Hold claim (C-id with status Hold) and the refusal sentence present for the off-ledger question.
- `git status` doesn't show `sessions/` or `.env`.

## Progress log

### 2026-10-15: Tasks 1–4 done. Tasks 0 and 5 blocked: no `GROQ_API_KEY` in `.env` yet
- **Env:** `python` isn't on PATH; use `python3`. Created `.venv/` (gitignored) with `openai` 3.31.0. Run LLM code with `.venv/bin/python`.
- **Task 1, `classify_eval.py`:**
  - Added `DEFAULT_MODEL = "openai/gpt-oss-120b"`, because llama-3.3-70b-versatile is shut down.
  - Added a stdlib `.env` reader at import time; real environment variables win.
  - New `make_client()` (shared with `converse.py`) uses `max_retries=4`, so the SDK backs off on 429.
  - The classifier now passes `response_format={"type":"json_object"}`.
  - Docstring now says `python3`/`.venv`.
  - Keyword baseline is unchanged at 34/48.
- **Task 2, `prompts/conversation_prompt.md`:** slots `{reason} {bucket} {bucket_name} {claims}`, filled with `str.replace`, not `.format`, because the JSON contains braces. It holds the status → phrasing table, the exact refusal sentence, the banned topics, the not-financial-advice line (first reply only), a limit of 2 claims per reply, and the JSON output format `{"reply", "claim_ids"}`.
- **Task 3, `converse.py`:**
  - `allowed_claims(bucket)` filters by bucket and drops `Hold` by prefix. Today that drops C31 from B5.
  - `check_reply(raw, allowed_ids)` is the guard: it rejects unparseable output and any cited ID outside the bucket. On failure the model gets one retry with the problem stated. If that fails too, the reply becomes `REFUSAL` and the log records `fallback: true`, plus a `violation` event for each bad attempt.
  - Flow: disclosure → T0 → reason → classify, with one follow-up if B0 (still B0 → end, logged `unclassified`) → up to 4 bot turns (`done` exits early) → T1. `--t2` appends the day-7 score and `looked_into_policy`.
  - Log events in `sessions/<pid>.jsonl`: `t0, reason, classify, assistant, user, violation, end, t1, t2`. Each assistant line carries `claim_ids, bucket, model, turn, fallback`.
  - `--selfcheck` runs offline asserts and passes.
- **Task 4:** `sessions/` added to `.gitignore`.
- **Still to do:** add the key → Task 0 (eval, record in CLAUDE.md) → Task 5 dry runs (B2, B3 with an off-ledger question, B0) → Task 6.

### 2026-10-15: Task 0 done
- `.env` created (chmod 600, gitignored). `.env.example` now names `openai/gpt-oss-120b`.
- Held-out: **48/48 primary, 7/7 secondary, 0 unneeded / 0 missed follow-ups.** Main test set: 109/110 (15/16 secondary). Passes the bar.
- Leakage check: none of the 3 few-shot examples in `classifier_prompt.md` appear in the held-out set.
- Caveat recorded in CLAUDE.md: both sets have the same author, and 100% means the set is saturated. Pilot answers will be the real test.
- Next: Task 5 dry runs (interactive; Som types as a fake participant).

### 2026-10-15: Task 5 dry runs (scripted stdin, logs in `sessions/test-b0|b2|b3.jsonl`)
- **B0** (`idk` → `never really thought about it`): one follow-up, still B0, the session ends and is logged `unclassified`. Correct.
- **Run 1 issues found:** claim IDs written inline "(C06)"; "the regulator" instead of IRDAI; questions pushing toward action ("migration process your insurer requires").
- **Run 2 (prompt: name the source, no IDs in text, no purchase/process questions) issues found:**
  - the refusal was paraphrased, not exact
  - "not financial advice" repeated every turn
  - **an unsupported claim**: "which means you can keep the same sum insured" (in no claim)
  - a question still nudged toward choosing an insurer
- **Fixes, moved into code where the rule must hold exactly:**
  - the model returns `"refuse": true`, and `check_reply` prepends the exact `REFUSAL` (selfcheck assert added)
  - the disclaimer is now in the intro, said once by code, and the prompt tells the model not to say it
  - prompt: "which means" may only restate a claim, never add consequences; example questions added
  - `temperature` 0.3 → 0, for reproducible logs
- **Run 3 result:**
  - B3 is clean: C10/C13 attributed correctly, "most claims rejected" answered with C10, "best insurer" and "costs double every 5 years" both got the exact refusal.
  - **B2 open issues**, left for the step-3 checker:
    1. Turn 1 states C08's content ("waiting periods start from zero") but cites only C06/C09, so the content and the cited IDs don't match. The guard can't see this.
    2. Inference claims (C06/C08) come out as "Which means …" sentence openers, often without naming IRDAI.
  - These are exactly the failures the unsupported-claims metric should count, so they're evidence for the write-up, not something to hide.
- These were informal R1/R2 probes, not the logged reversal runs (step 4).
