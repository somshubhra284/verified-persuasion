# Plan: Finish the build offline today (fixes 1 + 3 and every remaining build piece); test tomorrow

Saved to `.claude/tasks/finish-build.md` once approved.

## Context
The Groq daily limit is spent until tomorrow. Som wants every build step finished today, with **no LLM calls**, and all LLM testing tomorrow. "Done today" means the code is written and the offline self-checks pass. Anything that needs the model goes in a ready-to-run test script for tomorrow, ordered to fit the 200K tokens/day budget.

What's left to build:
- **Fix 1**: refuse an unsourced premise in the person's stated reason.
- **Fix 3**: the checker's blind spots, "right number, wrong population" and add-ons like "showing rapid cost growth". This also folds in the optional echo fix, since all three need the same gold rescore tomorrow.
- **The fixed-brief arm**: there's no way to run it yet.
- **Screening and consent at intake** for both arms.
- **Results analysis**: T0/T1/T2 per arm, plus unsupported claims.

Fix 2 (splitting C30's figure) wasn't chosen and stays open. Recruiting and the pilot need people, so they're out of scope.

## Tasks

### 1. Fix 1: premise check, enforced in code (`converse.py`, `prompts/conversation_prompt.md`)
The model already had a `refuse` flag and didn't use it for a stated premise. So instead of trusting a flag, every reply has to say what factual claim the person just made:
- The JSON gains two fields: `"premise": "<the factual claim in the person's last message, or null>"` and `"premise_claim": "<the ledger ID that supports it, or null>"`.
- In `check_reply`: if `premise` is non-null and `premise_claim` is null (or not an allowed ID), the code **prepends `REFUSAL`**, whatever `refuse` says. This also catches the R2-open path, where the premise *is* the reason.
- The `premise` text gets logged on the assistant event, so the write-up can show what was refused.
- The prompt adds a rule: opinions and feelings ("it's a waste", "I'm healthy") aren't premises. Only checkable facts are ("costs double every 5 years", "most claims are rejected").
- One more prompt rule, for the R2-open add-on: never characterise a claim's trend ("rapid", "keeps climbing"). State the numbers.
- New offline asserts: an unsupported premise → reply starts with REFUSAL; a supported premise (C10) → no refusal; no premise → unchanged.
- R1 nuance: "most claims are rejected" is a premise C10 *contradicts*. `premise_claim` = C10, so there's no blanket refusal, and the reply counters with C10. That's the behaviour we want.

### 2. Fix 3: checker blind spots (`check_claims.py`, `prompts/checker_prompt.md`, `data/checker_gold.jsonl`)
- Judge rule: "A number must describe the same population, period and measure as in the claim. A number from a figure's sub-group or total applied to a different group is unsupported."
- Judge rule: "Characterising words not in the claim ('rapid', 'keeps climbing', 'sizable', 'quickly eat into') make the sentence unsupported."
- **Echo fix**: the judge also gets the person's own words, so a number they said ("5 lakh") or a premise they stated, repeated back, is `non-factual`.
- Gold rows to add, about 8. All are from the real reversal logs or are close variants:
  - the R1 52% sentence (unsupported, wrong population)
  - the correct "about 6 in 10 formal awards" version (supported)
  - "showing rapid cost growth" (unsupported)
  - C17 stated plainly (supported)
  - "Those amounts can quickly eat into savings" (unsupported)
  - "86.9% of requests" (a rounding of C14's 86.88: **supported**, so the number check must not flag it; see below)
  - "a sizable share are upheld" (unsupported)
- Number check: accept a value that is the claim's number rounded to fewer decimals (86.88 → 86.9, 87). Offline assert added.
- The gold set grows from 30 to about 38. **Pass bar unchanged:** recall 100%, ≤ 2 false flags. Rescored tomorrow.

### 3. Intake: consent and screening (`converse.py`, shared by both arms)
- Before T0: the machine disclosure, then a consent yes/no (no → the session ends, logged `declined`).
- Screening, from the CLAUDE.md criteria:
  - age 22–45
  - has their own retail policy? (must be no)
  - covered by CGHS, ESIC or PM-JAY? (must be no)
- After T0: a T0 < 60 → `screened_out`.
- A screen-out ends politely and logs `screened_out` with the reason, so recruitment numbers are honest.
- The "working, urban" criteria are confirmed at recruitment, not here.

### 4. Fixed-brief arm (`converse.py <pid> --brief`, `data/fixed_brief.md`)
- Export the fixed brief from its Claude Docs artifact into `data/fixed_brief.md`. That's a docs read, not Groq. It becomes the file the arm shows, and git versions it.
- `--brief` flow: the same intake (consent, screening, T0, reason) → **classify the reason too** (so arms can be compared by bucket; this costs one LLM call, same as the system arm) → print the brief → "Press Enter when you've finished reading" → T1. The log records `arm: brief` and the time spent reading.
- The system arm logs `arm: system`. `--t2` is unchanged and works for both.
- **Assignment rule (default; change it if you prefer):** alternate by recruitment order, P01 system, P02 brief, and so on. The rule is written in CLAUDE.md before recruiting, so it can't be picked after the fact.

### 5. Results analysis (`analyze.py`, offline)
- Reads `sessions/P*.jsonl` and any `.check.jsonl` beside them.
- Prints a markdown table: pid · arm · bucket · T0 · T1 · T2 · ΔT1 · ΔT2 · looked into policy · factual sentences · unsupported claims.
- Then per arm: n, mean ΔT1, mean ΔT2, unsupported claims per conversation.
- Screened-out and declined sessions are counted separately.
- No significance tests: n is 5–7. The write-up says that plainly.
- Self-check: it builds 2 fake sessions in a temp dir and asserts the deltas and the per-arm means.

### 6. Tomorrow's test script (`docs/test-plan-day2.md`), ordered by value under the 200K-token budget
1. Run the self-checks (free).
2. `check_claims.py --gold` on the 38 rows (≈ 60K tokens) → must pass the bar before anything else is trusted.
3. Rerun R2-open ×3 and R1-open ×3 "after fix", plus their checks (≈ 80K).
4. `check_claims.py` on the old R2-mid logs (≈ 10K).
5. One dry run of the brief arm and one of the system arm, including screening (≈ 20K).
6. If tokens are left: R2-mid ×3 after the fix.

Each step lists the exact command and what passing looks like. If a step fails, stop and record it.

### 7. Housekeeping
CLAUDE.md (Status, Files, Commands, the assignment rule, next steps), task logs, the brief's `.md` docstring. Commit at the end.

## Not in this plan
Fix 2 (C30, your call). Recruiting and the pilot. Any LLM call today, beyond reading the brief from Claude Docs, which isn't Groq.

## Risks
- Fix 1 relies on the model filling `premise` honestly. If it writes null for a real premise, the code can't help. Tomorrow's R2-open reruns are the test, and a miss gets logged.
- Gold rows added after seeing the failures make the gold set easier for exactly those failures. The write-up should say the rescore is "after seeing the failures", not blind.

## Verification (today, offline)
- `converse.py --selfcheck`, `check_claims.py --selfcheck` and `analyze.py --selfcheck` all pass.
- A scripted `--brief` run up to the classify step, to check consent decline and screen-out paths without the API: a decline or screen-out ends before any LLM call, so those paths are fully testable today.
- `git status` is clean after the commit; `sessions/` isn't tracked.

## Progress log

### 2026-10-15: all 7 tasks done offline; LLM testing is in `docs/test-plan-day2.md`
- **Fix 1 (`converse.py`, `prompts/conversation_prompt.md`):**
  - The JSON has `premise` and `premise_claim`. `check_reply` now returns 4 values and prepends `REFUSAL` when `premise` is set and `premise_claim` isn't an allowed ID, whatever `refuse` says.
  - `premise` is logged on each assistant event.
  - Prompt rule 6: no characterising words; numbers only for the group the claim gives.
  - Asserts cover the unsupported premise, an off-bucket premise_claim, a contradicted premise (C10, no refusal) and no premise.
- **Fix 3 (`check_claims.py`, `prompts/checker_prompt.md`, gold):**
  - New judge rules: wrong population/period/measure; characterising words. The judge prompt's examples are **deliberately different from the gold phrases** ("soaring", "all ages vs young adults"), so the rescore tests whether the rule generalises rather than whether the judge memorised the phrases.
  - The judge gets "What the PERSON said so far" (the echo fix).
  - `in_pool()` accepts rounding (86.88 → 86.9/87).
  - Gold rows g31–g38 added (4 flagged): 38 rows, 16 flagged. These were written after seeing the failures, so the rescore isn't blind.
- **Intake (`converse.py intake()`), shared by both arms:**
  - consent → age → own policy → CGHS/ESIC/PM-JAY → T0 (< 60 screens out) → reason
  - Logs `declined` / `screened_out` with reasons. Tested offline: decline, age 50, own policy, T0 40, brief-arm T0 55. All correct, with no API call.
  - `ask_score` is reused for age (0–100 is fine for this range).
- **Brief arm (`--brief`):**
  - Same intake, then `classify_reason`, then the brief is printed, then Enter, then T1.
  - Logs `brief_read` with `seconds` and the `brief_sha` (12-char sha256) so the exact brief shown is traceable.
  - `data/fixed_brief.md` is a byte-exact export of the Claude Docs brief, **minus the C25 bullet and its source row**, with `\[` escapes removed. **The Claude Docs brief still has C25.**
- **`analyze.py`:** per participant (pid, arm, bucket, T0/T1/T2, ΔT1, ΔT2, looked, factual, unsupported), per arm (n, mean ΔT1, mean ΔT2 (n), looked, unsupported per conversation), and counts of declined/screened_out/unclassified/incomplete. The self-check builds 4 fake sessions in a temp dir.
- **Reversal inputs** now begin with the intake answers (yes, 30, no, no, T0 80 instead of 50). The conversation lines are unchanged. The day-1 logs used the old format.
- **Assignment rule** (alternate in recruitment order) is in CLAUDE.md Conventions.
- **Not tested:** anything that calls Groq. See `docs/test-plan-day2.md`.

## Follow-up, 15 Oct: fix 2 and the Docs brief (approved by Som)
- `data/ledger.json` C30 `figure`: "Health: 6,235 awards for complainant, 4,125 for insurer, 10,140 mediated (all lines: about 52%)" → "Health only: 6,235 awards for complainant, 4,125 for insurer (about 60%); 10,140 mediated". 6,235 / 10,360 = 60.2%, matching the claim's "about 6 in 10".
- Effect: 52 is no longer in any B3 claim, so `check_numbers` flags "52%" deterministically. The `check_claims.py` selfcheck assert now expects that flag. g31 in the gold set stays labelled unsupported.
- Ledger doc (Claude Docs): same figure change, plus a changelog row. The all-lines 52% remains in the Caveats table.
- Fixed brief (Claude Docs): removed the C25 premium bullet and its Sources row, so Docs now matches `data/fixed_brief.md` (that file is unchanged, so `brief_sha` is unchanged).
- Selfchecks: converse, check_claims and analyze all pass.
- Ledger doc bucket table: B2 "C06–C09, C25–C27" → "C06–C09, C26, C27 (C25 on hold)"; B4 "C08, C11, C15, C16, C25" → "C08, C11, C15, C16 (C25 on hold)", following the existing "(C31 on hold)" style.
