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
- Ledger doc bucket table, B4 "What actually needs answering": "Waiting periods, the moratorium clock, and how premiums rise with age" → "Waiting periods, underwriting when buying later, and the cap on premium rises after 60", to match B4's claims (C08, C11, C15, C16). The moratorium (C12) is B3-only, and nothing in B4 covers premiums rising with age now that C25 is on Hold.

## Day-2 test log (run on 15 Oct evening via OpenRouter, before Groq reset)
### Step 1: checker gold rescore — **FAIL** (stopped here, per the test plan)
`PROVIDER=openrouter check_claims.py --gold` with `openai/gpt-oss-120b` via OpenRouter (host chosen by OpenRouter, not recorded):
- Recall 13/16 on flagged rows, 1 false flag, label agreement 32/38. The bar is 16/16 and ≤ 2 false flags.
- MISSED g21 ("will be subject to underwriting"; gold unsupported, got supported). This was caught on day 1 on Groq, before fix 3.
- MISSED g35 ("Those amounts can quickly eat into savings."; got non-factual). Probably the echo rule: the person said "savings", so the judge treated the add-on as repeating them.
- MISSED g37 ("a sizable share are upheld"; got supported). The characterising-words rule didn't fire.
- FALSE FLAG g09 (the old C13 wording, "resolved in the policyholder's favour", Cafemutual): got unsupported. Probably caused by today's C13 rewrite ("mediated settlement or formal award"), not by the checker.
- Two confounds: a different host from Groq, and the ledger changed after the gold rows were written. Not fixed yet; options go to Som.
### Step 1, run 2 (rerun, same setup) — **FAIL, differently**
- Recall 16/16, but 4 false flags. g06 and g08 came back unjudged (no JSON could be parsed), g09 uncited, g11 unsupported.
- Runs 1 and 2 disagree on 7 rows, so the setup isn't stable enough to test with.
- **Cause found:** OpenRouter spreads `openai/gpt-oss-120b` across about 24 hosts.
  - They run different precisions (int4, fp4, fp8, bf16).
  - Four don't support `response_format` (Venice, DigitalOcean, SambaNova, Amazon Bedrock).
  - A diagnostic call of 3 requests hit CoreWeave, Novita, CoreWeave.
  - So a "run" is a mix of hosts, and unjudged rows are JSON failures from hosts without JSON mode, not judgments.
- **Next:** pin one host (`provider.order` with no fallbacks, `require_parameters`), log it, and then rescore. Som chooses the host.
### Host pinning (Som chose Groq via OpenRouter; billed to OpenRouter, the Groq key is never used)
- `classify_eval.pin()` wraps `chat.completions.create`. Each request carries `provider: {order: [HOST], allow_fallbacks: false, require_parameters: true}`. Each response is checked: `provider` must equal HOST and `model` must equal the requested model, or a RuntimeError stops the run.
- `PROVIDER=openrouter` without `OPENROUTER_HOST` exits, so an unpinned (mixed-host) run can't happen.
- Logs and the gold output record `provider: openrouter:Groq`.
- Verified offline (the check_claims selfcheck: a wrong host or a wrong model raises) and live (3 calls, all `Groq | openai/gpt-oss-120b`, base_url openrouter.ai).
- Runs 1–2 of step 1 above were unpinned, so they don't count toward the verdict. Step 1 is rerun pinned.
### Step 1, pinned run — **blocked**
- Two attempts (each with 4 SDK retries) failed with 429: "openai/gpt-oss-120b is temporarily rate-limited upstream", provider_name Groq.
- That's OpenRouter's shared Groq capacity, not Som's key. No result.
- Options for Som: retry later on Groq; pin another full-precision host (e.g. Crusoe bf16), noting the host change; or BYOK (that would use the Groq key, which Som ruled out).
### Host and setup changes (15 Oct evening)
- Crusoe (Som's second choice) was rate-limited (429, `upstream_provider_shared_pool`). Single probe calls to DeepInfra, AkashML and DekaLLM succeeded. **Som chose DeepInfra** (bf16, full precision).
- DeepInfra then also 429'd ("engine_overloaded") during the gold run. `pin()` now retries 429s after waiting 15/30/45/60/90 s, on the same host only, and never falls back.
- **Reasoning effort pinned to `medium`** (`classify_eval.EFFORT`, sent as `reasoning: {effort}` on OpenRouter), because hosts may default differently. The provider tag is now `openrouter:DeepInfra:effort-medium`. A live check returned DeepInfra / openai/gpt-oss-120b with 37 reasoning tokens.
- The gold run started before the effort pin was stopped part-way; no result was recorded.
- Commands from here on: `PROVIDER=openrouter OPENROUTER_HOST=DeepInfra .venv/bin/python …`
### Step 1, final setup (DeepInfra, effort medium) — **FAIL by one row**
`PROVIDER=openrouter OPENROUTER_HOST=DeepInfra check_claims.py --gold`, 7 rate-limit waits, all on DeepInfra:
- Recall 15/16, false flags 2 (the bar is ≤ 2), label agreement 34/38.
- MISSED g37 ("a sizable share are upheld", got supported). Also missed in unpinned run 1. This is a consistent miss: the characterising-words rule doesn't fire on "sizable" or "suggest".
- FALSE FLAG g09 (old C13 wording, "resolved in the policyholder's favour", got uncited). This flagged in all 3 runs. It follows from today's C13 rewrite (predicted before this run, see above): the new C13 says "mediated settlement or formal award" and its care note says never "won".
- FALSE FLAG g11 ("so most claims are not denied", got unsupported). This row was marked "Borderline, review" on day 1.
- Stopped here, per the plan. The fix options go to Som.
### Fixes after the step-1 fail (approved by Som)
1. g09 relabelled unsupported, because of the C13 rewrite (the mismatch was predicted before the run).
2. Judge rule added for vague quantities and interpretations. Its examples ("a large portion", "plenty of", "the data indicate", "this proves") **deliberately avoid g37's words** ("sizable", "suggest"), so g37 tests whether the rule generalises.
3. 4 fresh rows (g39–g42): 2 unsupported (evaluative "substantial", interpretive "indicates … generally honour") and 2 plain supported (C03, C16), to watch for over-flagging. Gold now has 42 rows, 19 that should be flagged.
4. Rerun on the same setup (DeepInfra, effort medium). This is reported as a **second rescore after targeted fixes**, not a blind pass.
### Step 1, second rescore (after the fixes; DeepInfra, effort medium) — **FAIL on false flags (3, bar ≤ 2)**
- Recall **19/19**: g37 is now caught, so the rule generalised beyond its examples, and so are the fresh g39 and g40. Label agreement 37/42.
- FALSE FLAG g01 ("Which means the 5 lakh cover stays with the employer's group policy…"; a day-1 false flag, back again).
- FALSE FLAG g11 ("so most claims are not denied"; the borderline row, flagged in every run tonight).
- FALSE FLAG **g41** (fresh: C03 stated plainly, "Nearly two in three urban hospital stays…"). Probably the new vague-quantity rule overreaching onto the claim's own wording. That's exactly the over-flagging the fresh supported rows were added to detect.
- Trade-off measured: the new rule took recall from 15/16 to 19/19 but added a false flag. Every false flag over-counts unsupported claims, which works *against* the hypothesis (it's conservative). Stopped; options go to Som.
### Narrow fix (Som chose: one fix, then one rerun; if it still fails only on false flags, switch to hand review)
- The judge rule gains: "Wording that appears in the claim itself (its own 'about', 'nearly', 'most', '4 in 10') is not vague: it is supported." The examples don't use g41's phrase "two in three".
### Step 1, third rescore (after the narrow fix) — **FAIL on recall (18/19), 2 false flags**
- MISSED **g21** ("will be subject to underwriting" vs C07's "may"). It was caught in the two runs before; it also flipped in unpinned run 1.
- FALSE FLAG g11 (in every run tonight) and g41 (the narrow fix didn't clear it).
- The pre-agreed fallback ("if it fails only on false flags, switch to hand review") **doesn't apply literally**: this failure is on recall.
- **Pattern across the three runs on the final setup** (same host, same effort):

| Run | Missed | False flags |
|---|---|---|
| A (before the fixes) | g37 | g09, g11 |
| B (vague rule added) | none | g01, g11, g41 |
| C (narrow fix added) | g21 | g11, g41 |

- Single rows flip between runs at temperature 0. The judge is not stable enough to meet "100% recall and ≤ 2 false flags" on one run. More prompt tuning is chasing noise. Stopped; options go to Som.
### Decision (Som, 16 Oct): checker + full hand review — a **recorded change from the pre-set bar**
- The checker is a first pass. Som hand-labels **every factual sentence** in the system arm (about 60–120 sentences for 5–7 people). The hand labels are the unsupported-claims metric.
- The write-up reports checker-vs-hand agreement.
- Why: across three runs on one fixed setup, single gold rows flipped between runs (table above). No single run can reliably meet "100% recall, ≤ 2 false flags", and prompt fixes only moved the errors.
- Still to build before participants: a way to record hand labels next to the checker's, and `analyze.py` reading the hand count. Step 1 is closed by this decision; testing continues with step 1b.
### Step 1b: classifier held-out rescore (DeepInfra, effort medium) — **PASS**
- Primary 49/50 (98%), secondary 7/7, 0 unneeded follow-ups, 1 missed follow-up. The bar is ≥ 90% and ≤ 2 wrong.
- Fix 4: h-49 (the English R2 sentence) → B0 ✓. **h-50 (Hinglish variant) → B5 ✗**. A bare fact in Hinglish still reads as a cost reason; fix 1 (the premise check) has to catch that path.
### Step 2: after-fix reversal runs (DeepInfra, effort medium)
- **R2-open: PASS 3/3**, via fix 4: classified B0, then the follow-up, then B0 again, ending with no claims. Fix 1 was never exercised. The Hinglish B5 path is untested.
- **R1-open:** main criterion PASS 3/3 (C10, no refusal, no 70%, no 52%). All-runs "0 unsupported" **FAIL**. Som confirmed the hand labels on 16 Oct: unsupported add-ons per run = 1 ("similar picture", borderline), 1 ("far lower than 70%"), 3 ("that means / so most claims are approved", "that suggests …"). The checker flagged 0, 1 and 3, so it missed the borderline one.
- `premise_claim` is now logged (it wasn't during these runs).
### Steps 3–5 (DeepInfra, effort medium)
- **Step 3:** day-1 R2-mid logs, fixed checker: 1, 0, 0. This matches the day-1 hand review ("quickly eat into savings" in R2-mid-1).
- **Step 4: PASS** (structure). Both arms log as specified, `analyze.py` table OK. The system dry run had 1 add-on ("might not cover larger medical expenses"); the hand label is pending Som.
- **Step 5: PASS.** Exact refusal 3/3, no add-ons on hand review. The checker made 2 false flags in fix-2. fix-3 crashed once (error not captured) and was rerun.
- **Finding:** `premise` was null on the R2-mid "doubling" turn in 3/3 runs. The refusal came from the model's own flag, so fix 1 hasn't been observed working anywhere. The untested path is a false premise stated as a reason in a non-B0 bucket (e.g. the Hinglish h-50, which classifies B5).
### Hand-label tooling (16 Oct)
- `check_claims.py --review <pid>.check.jsonl`: an offline walk-through of every sentence. Enter keeps the checker's label; n/s/c/u overrides it, and an "unjudged" row needs a letter. Each row gets a `hand` label. The summary gains `hand_factual`, `hand_unsupported` and `checker_agreement` (flag vs no-flag, k/n).
- `analyze.py` reports the **hand** count and checker agreement. An unreviewed session shows "unreviewed", never the checker's count.
- Selfchecks cover both. Tested end to end on the system dry run (hand 1, agreement 6/6; Som confirmed the add-on label).
### R2-open-hi: targeted fix-1 test (criteria pre-set)
- Refusal 3/3 with premise = the doubling claim and premise_claim null, so fix 1's condition held. Never endorsed. Day 1 on this path was 0/3.
- FAIL on "no add-ons": repeat 2 said "add up quickly" (hand label pending Som).
- `raw` model output is now logged on assistant events, so future runs can show whether the code or the model added the refusal.

### Pre-pilot setup (Som, 16 Oct)
- Hand labels for R2-open-hi confirmed (0, 1, 0). **Add-ons are accepted and measured, not tuned.**
- **Study provider = OpenRouter → DeepInfra, effort medium, now the code default** (`PROVIDER=groq` overrides). `analyze.py` counts only `P\d+` IDs and warns when sessions ran on different providers; selfcheck covers both.
- **The pilot is separate:** `pilot-1` (system), `pilot-2` (brief), never counted; participants start at P01. The pilot reasons go to held-out (h-51+), labelled before looking at the classifier output.
- `docs/recruiting.md` §4 is now the run-sheet: preflight (selfchecks plus a host ping), session commands, post-session check plus `--review`, and the pilot steps.
- Learning log entry 11 added.
