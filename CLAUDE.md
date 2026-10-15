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
- Assert only claims from `data/ledger.json`, and only those whose `buckets` include the person's primary or secondary bucket. **Exception (Som, 16 Oct):** when the person directly asks a factual question, any non-Hold claim that answers it may be used; it's logged as `question_claims`.
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
- `data/ledger.json`: 34 claims (C01–C34); C25 and C31 are Hold. The only source of facts. Change it only when a primary source is checked.
- `data/reasons_testset.jsonl` (110 answers) and `data/reasons_heldout.jsonl` (50 harder answers; h-49/h-50 added after the reversal runs): labelled "why" answers.
- `prompts/classifier_prompt.md`: the reason classifier prompt.
- `classify_eval.py`: scores classifiers (keyword baseline or LLM) on either set.
- **Live site:** https://somshubhra-verified-persuasion.static.hf.space (static HF Space serving `public/index.html`). The API is `app.py` on Render (https://verified-persuasion-f0vv.onrender.com, free, Singapore; it sleeps after 15 min). Data is in Supabase project `verified-persuasion` (ref `ykireedojkbfucxkjcxp`), table `events`. `export_sessions.py` pulls the data into `sessions/` and makes day-7 links. GitHub: https://github.com/somshubhra284/verified-persuasion (public). Pushing to main redeploys Render; **after changing `public/index.html`, upload it to the Space again**.
- `docs/learning-log.md`: where evidence changed the plan or the hypothesis (draft; add day-2 and participant results).
- `docs/recruiting.md`: invite, self-check, consent, day-7 message, debrief, recruiting log template.
- `docs/capstone-brief.md`: the 100x brief and its grading criteria.
- `converse.py`: both arms. Intake = consent + screening (age 22–45, no own policy, not CGHS/ESIC/PM-JAY, T0 ≥ 60) → reason → classify. The system arm argues from the bucket's claims; `--brief` shows `data/fixed_brief.md`. `--t2` for day 7. Logs go to `sessions/<pid>.jsonl` (gitignored).
- `check_claims.py` + `prompts/checker_prompt.md` + `data/checker_gold.jsonl` (42 rows): the unsupported-claims metric.
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
- Reversal runs (15 Oct; `docs/reversal-runs.md`, logs in `runs/reversal/`): R1 countered with C10 3/3. R2 mid-conversation got the exact refusal 3/3. **R2 as the opening reason failed 3/3**: it was classified B5, never refused, and C17 was spun into "rapid cost growth". All 3 R1 runs said "52% of health complaints" (C30's all-lines figure; health is 6 in 10), and the checker missed it. Fixes 1 and 3 were applied on 15 Oct, offline, and are **untested until day 2** (`docs/test-plan-day2.md`): (1) every reply reports the person's factual `premise`, and code prepends the refusal when no allowed claim covers it; no trend characterisation. (3) Judge rules for wrong-population numbers and characterisations; the judge sees the person's words (echo fix); the number check accepts rounding; gold is now 38 rows. Fix 2 done 15 Oct: C30's `figure` is health only (about 60%); the all-lines 52% is gone from the ledger, so the number check now flags "52%" by itself. The R2-mid checker counts are pending. Fix 4 (15 Oct, untested): a bare factual statement with no reason is B0 (classifier rule + h-49/h-50); re-score held-out on day 2.
- The five missing primary documents were downloaded on 15 Oct to `sources/` (gitignored; manifest in `.claude/tasks/offline-prep.md`). Checked and applied on 15 Oct: C03, C10, C12, C21 and C27 are now Primary. C10 is corrected: 3.26 crore was the number of claims paid, not the total. C08 now cites the original circular. C07 isn't repealed by the 2024 circular. C10's 2023–24 comparison is now its own claim, C34 (Secondary, IndiaMedToday). Both brief copies are updated. C13 and C16 were checked from the scanned PDFs and are now Primary. C13 had the wrong total in the news copy and now states its method. C30 now uses 2024–25 (about 56% of formal health awards went for the policyholder). All five primaries are checked.
- **Checker decision (16 Oct):** on one fixed setup (OpenRouter → DeepInfra, effort medium) the judge flipped single gold rows between runs: 15/16 then 19/19 then 18/19 recall, 2–3 false flags. Som chose **checker + full hand review**: every factual sentence in the system arm is hand-labelled, those labels are the metric, and checker agreement is reported. This is a recorded change from the pre-set bar.
- **Day-2 tests (16 Oct, OpenRouter → DeepInfra, effort medium; Groq not used).** Details: `docs/reversal-runs.md` "After fix", `.claude/tasks/finish-build.md`.
  - Classifier held-out 49/50 PASS. h-49 → B0 ✓; the Hinglish h-50 → B5 ✗.
  - R2-open PASS 3/3, via fix 4 (B0, then the follow-up, then the end, with no claims).
  - R1-open: main criterion PASS 3/3 (C10, no 52%, no 70%), but the hand count of unsupported add-ons was 1, 1, 3 ("so most claims are approved" and similar; confirmed by Som).
  - R2-mid PASS 3/3 (exact refusal, no add-ons).
  - Both arms dry-run OK.
  - **Fix 1 not yet observed working:** `premise` stays null when the false premise is phrased as a question, and R2-open never reached it.
  - Then: hand-review tooling built (`--review`). R2-open-hi (Hinglish, B5): refusal 3/3 with premise reported (fix 1's condition met; day 1 was 0/3), and 1 add-on ("add up quickly"; Som-confirmed hand labels 0, 1, 0).
  - **Decision (Som, 16 Oct):** persuasive add-ons ("that means…", "quickly") are accepted and **measured**, not tuned away; they're what the hand-reviewed metric counts.

## Next steps, in order
1. ~~Run the LLM classifier~~ (done, see Status).
2. ~~Conversation loop~~ (built and dry-run, see Status).
3. ~~Post-hoc checker~~ (done, see Status). Optional: give the judge the user's words to fix echo false flags, then rescore on gold.
4. ~~Reversal runs and day-2 tests~~ (done 16 Oct; see Status).
5. **Pilot next (on the live site):** send `…static.hf.space/?pilot=1` to 2 friends; the site gives pilot-1 (system) and pilot-2 (brief). Follow `docs/recruiting.md` §4. Add their "why" answers to the held-out set (label first). Fix anything before P01.
6. Run participants through the live link (the site gives P-numbers and arms). After sessions: `export_sessions.py`, then `check_claims.py` + `--review`, then `analyze.py`. Day 7: `export_sessions.py --t2-link P0N`.
7. Capstone submission: live link ✓, GitHub ✓; still to do: demo video, case study. Write up honestly, including a null result. Keep a log of where evidence changed the hypothesis, since the brief's Learning criterion rewards it.

## Conventions
- Show money in both INR and USD (≈ ₹96.8 per $1, rate as of 10 Oct 2026).
- Keep it small: the brief says one conversation that moved a real belief beats six components without receipts.
- API key lives in `.env` (never commit it; scripts read it themselves). Default model `openai/gpt-oss-120b` on Groq's free tier. Use `.venv/bin/python` (`python` isn't on PATH).
- **Study provider (Som, 16 Oct): OpenRouter → Cerebras, reasoning effort medium, for the pilot and every participant.** (Switched from DeepInfra the same day: median reply 1.0 s vs 30–60 s, with the same premise handling. Re-validated in `runs/chat-quality/`.) This is the code default (needs `OPENROUTER_API_KEY` in `.env`); `PROVIDER=groq` overrides it. The code pins the host, retries 429s on the same host, and stops if any other host or model answers. `analyze.py` warns if sessions ran on different providers. Every log records `provider`; don't pool results across providers without saying so.
- Groq free tier: 200K tokens/day (rolling). The 9 reversal runs plus checks used about a day's budget. Plan participant sessions and checker runs on separate days if needed.
- **Arm assignment (fixed before recruiting):** alternate in recruitment order: P01 system, P02 brief, P03 system… Screened-out or declined people don't take a number. The pilot (`pilot-1` system, `pilot-2` brief) is separate and never counted; participants start at P01.
- Commands: `.venv/bin/python classify_eval.py [--heldout] [--llm]` · `.venv/bin/python converse.py <pid> [--brief] [--t2]` · `python3 analyze.py` · `converse.py --selfcheck` · `.venv/bin/python check_claims.py sessions/<pid>.jsonl` · `check_claims.py --review sessions/<pid>.check.jsonl` (hand labels = the metric) · `check_claims.py --gold`
