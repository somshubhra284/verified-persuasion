# Plan: offline prep, 15 Oct 2026 (no Groq calls)

Three items that don't need the model. Status: **approved 15 Oct (B0 for fix 4); items 2 and 3 done, item 1 waiting on Som's downloads.**

## 1. Primary documents (Som downloads; I verify)
The IRDAI and Ombudsman sites block bots, so the files have to be opened by hand. Here are the five (from the Sources section of the ledger doc):

| # | Document | Where | What it settles |
|---|---|---|---|
| 1 | IRDAI Annual Report 2024–25 | [listing](https://irdai.gov.in/document-detail?documentId=8375620) | C10, C21, C27 → Primary |
| 2 | IRDAI Master Circular on Health Insurance Business, 29 May 2024 | irdai.gov.in | replaces the copies behind C08, C12; settles C07 |
| 3 | Council for Insurance Ombudsmen Annual Report 2024–25 | cioins.co.in | C13 |
| 4 | NSS 80th round full report tables (MoSPI) | mospi.gov.in | C03; confirms the C28 chart reading |
| 5 | IRDAI senior-citizen premium circular, Jan 2025 | [listing](https://irdai.gov.in/web/guest/document-detail?documentId=6639156) | C16 |

- **Som:** save the PDFs into `sources/`. I'll add `sources/` to `.gitignore` so large PDFs stay out of git; the URLs already sit in the ledger.
- **Me, once they're there:** read each PDF and check every claim it covers, word for word and number by number. I'll propose `status` / `figure` / `source` changes and wait for your yes before touching `ledger.json` (the CLAUDE.md rule: change it only when a primary source is checked). Then I'll mirror the changes in the ledger doc's changelog.
- If a number disagrees, the claim goes to Hold until you decide.

## 2. Fix 4: how to classify "Hospital costs in India double every five years"
**Recommendation: B0.** The classifier then asks one follow-up to get the person's real reason, and Fix 1 refuses the premise either way.
- **Why B0:** the sentence gives no reason for not needing a policy. If anything, it argues *for* one. The R2-open pass criterion, set before any run, assumed B0. Labelling it B5 would mean the system argues from cost claims the person never raised.
- **Changes:**
  - `prompts/classifier_prompt.md`: add a rule: "A bare factual statement that gives no reason for not needing a policy is B0." Add one example (not the R2 wording; e.g. "medical inflation in India is 14% a year" → B0).
  - `data/reasons_heldout.jsonl`: add 2 rows: the R2 sentence (B0) and one Hinglish variant (B0). Mark them `"note": "added after reversal runs"`, since they were written after seeing the failure.
- **Cost tomorrow:** rerun the held-out eval (50 rows, ~15K tokens) to check the rule didn't break other buckets. Bar unchanged (≥ 90%, ≤ 2 wrong). I'll add it to `docs/test-plan-day2.md` as step 1b, before the reversal reruns, since the R2-open rerun depends on it.
- **Alternative (B5):** no prompt change, add the row labelled B5, no extra eval. It's cheaper, but it leaves the system arguing about savings with someone who didn't mention them.

## 3. Recruiting materials (`docs/recruiting.md`)
One file, to copy and paste into WhatsApp or DMs:
1. **Invite** (~60 words): a 10-minute chat with a computer program about one belief on health insurance, plus a 1-minute follow-up on day 7. No selling, no names kept. It **does not** mention the hypothesis, the two arms, or "persuasion", so neither arm is primed.
2. **Self-check before booking:** age 22–45, working, lives in a city, no health policy in their own name, not on CGHS/ESIC/PM-JAY. This saves screen-outs; the program re-asks anyway.
3. **Consent line:** the same words as the disclosure in `converse.py` intake, so what they agree to beforehand matches what they see.
4. **Day-7 message** for T2: score + "Did you look into a policy this week?", matching `--t2`.
5. **Debrief** (sent after T2): what the study tested, that there were two versions, and that this isn't financial advice.
6. **Recruiting log template:** a table of pid · date · arm (from the alternation rule) · T0 done · T2 due date · T2 done. It stays out of git, under `sessions/`, because it holds names.

## Not in this plan
Any Groq call. Pilot and participants. Editing the ledger before the PDFs are checked.

## Change log
- `.gitignore`: added `sources/` (primary PDFs, item 1).
- **Fix 4:**
  - `prompts/classifier_prompt.md` rule 2 now ends: "A bare factual statement that gives no reason for not needing a policy (a fact about prices, hospitals or the industry) is also B0."
  - New example: "medical inflation in India is 14% a year" → B0 with a follow-up. Deliberately not the R2 wording.
  - `data/reasons_heldout.jsonl` gains h-49 (the R2 sentence) and h-50 (a Hinglish variant), both B0, with `note: added after reversal runs`. There are now 50 rows.
  - The offline keyword eval runs on all 50.
  - `docs/test-plan-day2.md` gains step 1b, the LLM held-out re-score (same bar); step 2 depends on it.
- **Recruiting:** `docs/recruiting.md` has the invite, self-check, consent, how to run each arm, the day-7 message, the debrief and a recruiting log template (kept at `sessions/recruiting-log.md`, which is gitignored).
- `converse.py` disclosure: added "You can stop at any time (Ctrl-C)." so the consent text matches the program word for word. A stopped session is logged as incomplete.
