# Plan: Post-hoc claim checker (CLAUDE.md next step 3)

Saved to `.claude/tasks/claim-checker.md` once approved.

## Context
The hypothesis needs a number: **unsupported claims per conversation**. `converse.py` already guards cited IDs, so a cited ID must belong to the bucket. The guard can't see what a reply actually *says*. Dry run B2 proved the gap: a reply stated C08's content ("waiting periods start from zero") while citing only C06/C09. An earlier run invented "you can keep the same sum insured", which is in no claim at all. The checker reads the logged replies after the fact and counts these. It also answers brief question 4, "How would you notice an unsupported claim, and how fast?"

## Design: two layers, one file `check_claims.py`
**Layer 1, numbers (deterministic, free).** Pull every number out of each assistant reply: digits, %, ₹ amounts, lakh/crore, and the number words "zero" to "ten", so "four in ten" and "4 in 10" match. Each number must appear in the `claim` or `figure` of a **cited** claim. Otherwise:
- `echo`: the number appeared in the person's own earlier messages ("5 lakh group cover"). Not counted.
- `uncited`: the number is in another allowed claim the reply didn't cite.
- `unsupported`: the number is in no allowed claim.

Ceiling: it catches wrong or invented numbers only, not wrong words.

**Layer 2, sentences (LLM judge).** For each reply, one call to the same Groq model with the reply split into sentences, the cited claims and the bucket's other allowed claims. Each sentence gets one label:
- `non-factual`: a question, empathy, the refusal or the disclaimer
- `supported`: by a cited claim; gives the ID
- `uncited`: supported only by an allowed claim the reply didn't cite; gives the ID (the C08 case)
- `unsupported`: no claim says it; includes "which means" add-ons beyond the claim

Output is JSON mode with one label per sentence. Only the bucket's claims are sent, not all 33, which keeps a call at about 1.5K tokens, under the 8K tokens/min limit.

**Metric per session:** factual sentences, supported, uncited, unsupported, and the Layer 1 number flags. **Unsupported claims = unsupported + uncited** (both break "every factual sentence names its source"). Both are reported separately too. A sentence flagged by either layer counts once.

## The judge must be checked before its numbers mean anything
Same discipline as the classifier: a small gold set and a pass bar set **now**.
- `data/checker_gold.jsonl`: about 30 sentences, each `{sentence, cited_ids, bucket, label}`. Sources: the sentences from the three dry-run logs; the two known failures from the earlier runs ("keep the same sum insured", the C08-content-cited-as-C06/C09 sentence); and about 6 sentences I'll write to trip it, such as a wrong figure ("12% rejected"), a right fact cited with the wrong ID, an off-bucket claim, and a bare "which means" add-on.
- **I draft the labels, and you review them** before the gold set counts. A gold set written and graded by the same author is the same weakness the classifier sets have, and I'll note that.
- **Pass bar:** the judge catches every `unsupported`/`uncited` sentence in gold (recall 100%), with ≤ 2 false flags. If it misses, the fix is the prompt; then rerun.

## Tasks
1. `prompts/checker_prompt.md`: label definitions, a status-aware reading ("which means" must restate the claim), JSON output `{"sentences": [{"text", "label", "claim_id"}]}`.
2. `check_claims.py` (about 90 lines), reusing `make_client`, `DEFAULT_MODEL` and `HERE` from `classify_eval.py` and `LEDGER`/`allowed_claims` from `converse.py`:
   - `numbers(text)`: number extraction + normalization; `check_numbers(reply, cited, allowed, user_text)` → flags
   - `judge(reply, cited, allowed)` → sentence labels
   - `python check_claims.py sessions/P01.jsonl [...]`: prints each flagged sentence with its reason and a per-session summary line, and writes `sessions/<pid>.check.jsonl` (gitignored with the rest)
   - `python check_claims.py --gold`: scores the judge on the gold set against the bar
   - offline self-check asserts in `__main__` for `numbers()` / `check_numbers()`: "four in ten" == "4 in 10", "₹24,000" == "24000", the 5 lakh echo isn't flagged, and "12%" against C10 is flagged
3. Draft `data/checker_gold.jsonl` → **pause for your label review**.
4. Run `--gold`, and fix the prompt if it's below the bar (each attempt is logged, not hidden).
5. Run the checker on `sessions/test-b2.jsonl` and `test-b3.jsonl`. The B2 C08 sentence should come out `uncited`.
6. Update CLAUDE.md (Status, Commands, step 3 struck through) and the task file's change log.

## Not in this plan
Running the checker live inside `converse.py` to block bad replies. That's tempting, but it would change the system under test mid-study. Decide after the pilot. The fixed-brief arm isn't checked, because it's static and was verified by hand.

## Risks
- The judge is an LLM grading an LLM, the same model family. The gold set and the bar are the defence; the write-up says so.
- The free tier allows about 2 judge calls a minute, so a 4-reply session takes about 2 minutes. Fine for 7 participants.

## Verification
- `.venv/bin/python check_claims.py --selfcheck`: the asserts pass, offline.
- `--gold` meets the bar (recall 100%, ≤ 2 false flags), with the result recorded in CLAUDE.md.
- On `test-b2.jsonl`, the C08 sentence is flagged `uncited`. On `test-b3.jsonl`, there are no flags, and the refusals are `non-factual`.

## Progress log

### 2026-10-15: Tasks 1–3 done; paused for Som's gold-label review
- **`prompts/checker_prompt.md`:** 4 labels. A stronger word ("will" for "may", "never") counts as not supported. A mixed sentence takes its worst part. Judge only against the given claims. JSON `{"sentences":[{n,label,claim_id,why}]}`.
- **`check_claims.py`:**
  - `numbers()`: digits with Indian commas normalized; number words only as "X in Y" ratios or "zero" (bare "one"/"two" are too common to flag).
  - `check_numbers()`: each number must be in a cited claim's claim/figure/source. Otherwise it's `echo` (the user said it; ignored), `uncited` (in another bucket claim) or `unsupported`.
  - `judge()`: one call per reply, sending the cited claims plus the bucket's other claims.
  - `check_reply()`: each sentence takes the worse of the judge and number labels. If the judge skips a sentence, it's `unjudged` and counts as flagged.
  - `check_session()`: prints the flags and writes `sessions/<pid>.check.jsonl` plus a summary line. `unsupported_claims = uncited + unsupported + unjudged`.
  - `--gold`: scores recall on the flagged rows, false flags and label agreement, against the bar.
  - Self-check asserts pass. They include the C08 "from zero" case, caught as `uncited` by numbers alone.
  - Fixed a bug: non-factual sentences were being counted in `factual_sentences`.
- **`data/checker_gold.jsonl`:** 30 rows (13 dry-run, 3 earlier-run failures, 14 adversarial); 12 should be flagged. Each row has a `note` with the reasoning. **These are Claude's drafted labels, so they count only after Som reviews them.** g11 is marked borderline.
- **Ledger issue found (not fixed; Som's call):** C25 (B2) quotes premiums (₹9,192 / ₹12,590), but the hard rules say never quote premiums.

### 2026-10-15: Tasks 4–6 done
- Som approved the gold labels as drafted.
- **C25 → Hold** (Som's decision). Status is now `Hold (quotes premiums, against hard rules; source Primary, chart undated)`. C25 was in B2 **and B4**, so it leaves both. B2 is now C06–C09, C26, C27. The Claude Docs ledger doc still needs the same change in its changelog.
- **Gold (first run, no prompt tuning): PASS at the edge.** Recall 12/12, false flags 2/2 allowed, label agreement 28/30.
  - g01: the judge flags "5 lakh" because it never sees the user's words. The number layer handles echoes; the judge doesn't.
  - g11: the judge treats "so most claims are not denied" as an add-on.
- **Dry runs:**
  - test-b2: 6 factual sentences, 2 flagged. The C08 leak is caught as `uncited` by **both** layers. The "5 lakh" echo is a false flag.
  - test-b3: 4 factual sentences, 1 flagged. That's g11's sentence, also a false flag.
  - So the true counts are 1 and 0. The checker errs on over-counting, which is conservative: it can only make our system look worse, not better.
- **Follow-up, not done:** pass the user's words to the judge, then **rescore on gold** before trusting the change. Tuning after seeing gold results risks fitting the gold set, so it gets a fresh run and a note in the write-up.
