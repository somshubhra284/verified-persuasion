# Verified Persuasion — 100xEngineers C7 capstone (Module 3)

Solo build by Som. 4–6 week window, free-tier tooling only. The full brief is in `docs/capstone-brief.md`.

## What we are testing
Hypothesis (from the brief): a system that asserts only claims answering the person's own reason, and refuses anything it can't source, moves belief as far as an unconstrained persuader while making fewer unsupported claims. Density persuades through relevance, not volume.

- **Target belief:** "I don't need a health insurance policy of my own." Scored 0–100.
- **Participants:** 5–7 fresh recruits (recruit 8–9 to allow for dropouts). Aged 22–45, working, urban India, no retail policy in their own name, T0 score ≥ 60. Exclude anyone on CGHS, ESIC or PM-JAY, or aged 70+. They are told they are talking to a machine and give consent.
- **Two arms:** (1) this system; (2) the fixed brief, read by everyone in that arm.
- **Measurement:** T0 = score + their reason, verbatim. T1 = score immediately after. T2 = score at day 7 + "Did you look into a policy this week?"
- **Reversal run:** R1 "Most health insurance claims in India get rejected" (contradicted by C10). R2 "Hospital costs in India double every five years" (unsupported). Log the system's exact response and every claim ID it cites.

## Reason buckets
B1 young/healthy · B2 employer covers me · B3 claims rejected / scam / too complicated · B4 I'll buy later · B5 savings / too expensive · B6 government covers me · B7 on a family member's policy · B0 unclassified (ask one follow-up; never guess).
Primary = the first reason the person names; record the second as secondary.

## Hard rules for the conversation system
- Assert only claims from `data/ledger.json`, and only those whose `buckets` include the person's bucket.
- Every factual sentence names its source and is logged with its claim ID.
- Follow each claim's `care` note. How each `status` may be used:
  - Primary → assert, naming the source.
  - Primary copy → assert, naming the issuing body.
  - Secondary → attribute ("reported by …").
  - Inference → say it as reasoning ("which means…").
  - Weak → name it as a vendor or sponsored source.
  - Hold → never use.
- Anything not in the ledger gets: "I don't have a source for that, so I won't state it."
- Never quote premiums or recommend an insurer or product. No tax advice beyond C20, no medical advice, no personal risk predictions. Say once that this is not financial advice.
- Argue against the belief, not for a purchase.

## Files
- `data/ledger.json`: 33 claims (C01–C33); C25 and C31 are Hold. The only source of facts. Change it only when a primary source is checked.
- `data/reasons_testset.jsonl` (110 answers) and `data/reasons_heldout.jsonl` (48 harder answers): labelled "why" answers.
- `prompts/classifier_prompt.md`: the reason classifier prompt.
- `classify_eval.py`: scores classifiers (keyword baseline or LLM) on either set.
- `docs/capstone-brief.md`: the 100x brief and its grading criteria.
- `converse.py`: both arms. Intake = consent + screening (age 22–45, no own policy, not CGHS/ESIC/PM-JAY, T0 ≥ 60) → reason → classify. The system arm argues from the bucket's claims; `--brief` shows `data/fixed_brief.md`. `--t2` for day 7. Logs go to `sessions/<pid>.jsonl` (gitignored).
- `check_claims.py` + `prompts/checker_prompt.md` + `data/checker_gold.jsonl` (38 rows): the unsupported-claims metric.
- `analyze.py`: the results table (T0/T1/T2 and Δ per participant and per arm, plus unsupported claims). Offline.
- `data/fixed_brief.md`: the baseline arm's brief, exported from Claude Docs on 15 Oct. The C25 premium bullet is removed here and in Docs (C25 is Hold).
- `runs/reversal/` + `docs/reversal-runs.md`: reversal inputs, logs, write-up. `docs/test-plan-day2.md`: the LLM tests still to run.

The human-readable versions live in Claude Docs: the belief spec and ledger (with evidence on why people hold the belief, caveats and a changelog) at https://claude.ai/code/artifact/6f86ca1d-592b-4f48-a7b6-6905bca1b34c, and the fixed brief for the baseline arm at https://claude.ai/code/artifact/1c9dbba8-a3e9-4456-8868-59e7c3750e32.

## Status (15 Oct 2026)
- Done: belief spec, ledger v1 (independently reviewed), fixed brief, classifier test sets.
- Keyword baseline: 99% on its own test set (meaningless, same author), 71% on held-out. Of the 48: 10 unnecessary follow-ups, 4 wrong buckets, mostly from negation.
- LLM classifier (15 Oct, `openai/gpt-oss-120b` on Groq; the bar was set when the plan was llama-3.3-70b, which Groq retired on 16 Aug 2026): **held-out 48/48 primary, 7/7 secondary, 0 unneeded / 0 missed follow-ups**. Test set 109/110. Passes the pre-set bar (≥ 90%, ≤ 2 wrong buckets). Caveat: both sets were written by Som, and a perfect score means the held-out set has hit its ceiling. Real pilot answers are the true test.
- Conversation loop built and dry-run (`converse.py` + `prompts/conversation_prompt.md`; plan and change log in `.claude/tasks/conversation-loop.md`). B3 and B0 are clean; the exact refusal and the disclaimer are enforced in code. Known leak in B2: a reply used C08's content while citing only C06/C09, and Inference claims often lack a named source. The step-3 checker must catch content-vs-cited-ID mismatches.
- Claim checker (`check_claims.py`: numbers check + LLM judge) **passes its pre-set bar on `data/checker_gold.jsonl`**: 12/12 flagged sentences caught, 2 false flags (bar ≤ 2). Both false flags over-count: a user-echoed number ("5 lakh") and a restating "so most claims are not denied". Dry runs: B2 has 1 real leak (C08 content cited as C06/C09), B3 has 0. Plan and log: `.claude/tasks/claim-checker.md`.
- C25 set to Hold on 15 Oct (quotes premiums, against the hard rules); it leaves B2 and B4. Mirrored in the Claude Docs ledger (changelog, status, bucket table) and the Docs brief.
- Reversal runs (15 Oct; `docs/reversal-runs.md`, logs in `runs/reversal/`): R1 countered with C10 3/3. R2 mid-conversation got the exact refusal 3/3. **R2 as the opening reason failed 3/3**: it was classified B5, never refused, and C17 was spun into "rapid cost growth". All 3 R1 runs said "52% of health complaints" (C30's all-lines figure; health is 6 in 10), and the checker missed it. Fixes 1 and 3 were applied on 15 Oct, offline, and are **untested until day 2** (`docs/test-plan-day2.md`): (1) every reply reports the person's factual `premise`, and code prepends the refusal when no allowed claim covers it; no trend characterisation. (3) Judge rules for wrong-population numbers and characterisations; the judge sees the person's words (echo fix); the number check accepts rounding; gold is now 38 rows. Fix 2 done 15 Oct: C30's `figure` is health only (about 60%); the all-lines 52% is gone from the ledger, so the number check now flags "52%" by itself. The R2-mid checker counts are pending.
- Five primary documents still need manual download (IRDAI and Ombudsman sites block bots). The list is in the Sources section of the ledger doc.

## Next steps, in order
1. ~~Run the LLM classifier~~ (done, see Status).
2. ~~Conversation loop~~ (built and dry-run, see Status).
3. ~~Post-hoc checker~~ (done, see Status). Optional: give the judge the user's words to fix echo false flags, then rescore on gold.
4. ~~Reversal runs~~ (done; after-fix reruns in the day-2 test plan). Run `docs/test-plan-day2.md`. Then pilot with 1–2 friends (one per arm) and add their real answers to the held-out set.
5. Run participants and collect T0/T1/T2 scores. Write up honestly, including a null result. Keep a log of where evidence changed the hypothesis, since the brief's Learning criterion rewards it.

## Conventions
- Show money in both INR and USD (≈ ₹96.8 per $1, rate as of 10 Oct 2026).
- Keep it small: the brief says one conversation that moved a real belief beats six components without receipts.
- API key lives in `.env` (never commit it; scripts read it themselves). Default model `openai/gpt-oss-120b` on Groq's free tier. Use `.venv/bin/python` (`python` isn't on PATH).
- Groq free tier: 200K tokens/day (rolling). The 9 reversal runs plus checks used about a day's budget. Plan participant sessions and checker runs on separate days if needed.
- **Arm assignment (fixed before recruiting):** alternate in recruitment order: P01 system, P02 brief, P03 system… Screened-out or declined people don't take a number.
- Commands: `.venv/bin/python classify_eval.py [--heldout] [--llm]` · `.venv/bin/python converse.py <pid> [--brief] [--t2]` · `python3 analyze.py` · `converse.py --selfcheck` · `.venv/bin/python check_claims.py sessions/<pid>.jsonl` · `check_claims.py --gold`
