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

### Item 1: downloads (15 Oct, done by Claude with curl and a browser user-agent; no browser needed)
All five are in `sources/` (gitignored). Each was checked to be the right document from its title page or text:

| File | Pages | Text extractable? | From |
|---|---|---|---|
| IRDAI-Annual-Report-2024-25.pdf | 416 | yes (Hindi half in a legacy font; English from about p. 250) | irdai.gov.in document-detail?documentId=8375620 |
| IRDAI-Master-Circular-Health-29-May-2024.pdf | 17 | yes | irdai.gov.in document-detail?documentId=4942918 (ref IRDAI/HLT/CIR/PRO/84/5/2024) |
| IRDAI-senior-citizen-premium-circular-Jan-2025.pdf | 3 | **no, scanned** | irdai.gov.in document-detail?documentId=6639156 |
| CIO-Annual-Report-2024-25.pdf | 98 | **almost none, images** | cioins.co.in/annualreports/AnnualReport2024-2025.pdf |
| NSS-Report-596-Household-Social-Consumption-Health.pdf | 128 | yes | mospi.gov.in, NSS Report no. 596 (80/Health) |

- Added `pypdf` to `.venv` for text extraction. It's a checking tool only; the scripts don't import it.
- The two scanned files need page images to verify. `sips` renders only page 1, so use `brew install poppler` (which also lets the Read tool show PDF pages).
- Next: verify each claim against its PDF and propose ledger changes for Som's approval.

### Item 1: verification of the text-readable PDFs (15 Oct) — APPROVED and APPLIED (see below)
Also downloaded `sources/IRDAI-Master-Circular-Health-29-May-2024-Annexures.pdf` (46 pp), for Annexure-6, the list of circulars it repeals.
Page refs below are PDF page numbers (printed page in brackets).

| Claim | Verdict | Evidence | Proposed change |
|---|---|---|---|
| C10 | **Wording error + unverifiable part** | IRDAI AR 24–25 p.274 [42], para I.6.5.6 and Table I.29 (p.275): 372.58 lakh claims in total; 326.01 lakh paid (87.50%), 29.51 lakh repudiated (7.92%), 17.07 lakh pending (4.58%). **3.26 crore is the number settled, not the total.** FY24 (83/11/6) isn't in this report. | claim: "Of about 3.7 crore health claims handled in 2024–25, 87% were paid, 8% were repudiated and about 5% were still pending at year end." figure: "372.58 lakh claims; 326.01 lakh paid (87.5%), 29.51 lakh repudiated (7.9%), 17.07 lakh pending (4.6%)". Status → Primary; source → IRDAI AR 2024–25, para I.6.5.6 and Table I.29. **Drop "down from 11%"** (or keep it as a separate Secondary claim, Som's call). |
| C21 | Confirmed | p.274 [42], para I.6.5.5: "average amount paid per claim was ₹28,910". FY24 ₹31,086 isn't in this report. | Status → Primary; figure → "₹28,910 per claim paid"; drop the FY24 figure. |
| C27 | Confirmed (unit: lives) | p.272, Table I.26 and para I.6.5.3: lives covered 5,806.47 lakh; group 2,751.01 lakh (47.4%); individual 601.46 lakh (10.3%); government 2,454.00 lakh (42.3%). | Status → Primary. claim: "people" → "lives covered" (a person on two policies counts twice). |
| C07 | Still copy-only, but not repealed | The 2024 Master Circular has no group-to-individual underwriting rule. Its Annexure-6 repeal list **does not include** IRDAI/HLT/REG/CIR/003/01/2020. | Keep Primary copy. care: replace "the 2024 Master Circular may supersede this" with "Not in the 2024 Master Circular's repeal list (Annexure-6)". Upgrading needs the 2020 circular itself from irdai.gov.in. |
| C08 | Confirmed as inference | MC paras 11 (migration, explicitly "including … group insurance policies") and 12d (portability) are the only routes for credits to transfer, pp.7–8. | Status stays Inference; source/url → the IRDAI original (document-detail?documentId=4942918), paras 11–12. |
| C12 | Core confirmed; two figure details unsourced | MC para 13, p.8: not contestable on non-disclosure/misrepresentation, except established fraud, after "60 months of continuous coverage"; ported/migrated credits count. "(was 96)" and "on the original sum insured" are not in it. | Status → Primary; figure → "60 months of continuous coverage; ported and migrated credits count". Claim text unchanged ("exclusions still apply" follows because para 13 only bars non-disclosure challenges). |
| C03 | Confirmed | NSS Report 596, p.47 [21], section 2.3.2: hospitalisation cases (excluding childbirth), private hospital incl. govt-empanelled: urban 64.6%, rural 57.9%. | Status → Primary; source → NSS Report 596, section 2.3.2. care: "Excludes childbirth; private includes government-empanelled hospitals." |
| C28 | Confirmed | NSS Report 596, p.50 [24]: any scheme, urban 19.1 (2017–18) → 44.3 (2025); rural 14.1 → 47.4. | No change (already Primary via the press note); optionally add the report as a second source. |

#### Applied 15 Oct (Som approved; C10's FY24 "down from 11%" dropped, per Claude's recommendation, since Som didn't choose)
- `data/ledger.json`: every change in the table above. Edited field by field, because the file is hand-formatted. C28 is unchanged.
- `data/fixed_brief.md` and the Claude Docs brief now have the same four bullets reworded (C03, C10, C21, C27). The C03, C08/C12 and C10/C21/C27 source links point to the primaries, and the separate C27 sources row was merged into the C10/C21 row. **`brief_sha` changes**: no participant has seen the old brief yet.
- `data/checker_gold.jsonl` g22: the sentence now says "lives covered … were under individually bought policies", to match C27's new wording. The label (supported) is unchanged.
- Ledger doc (Claude Docs):
  - The claim table rows for C03, C07, C08, C10, C12, C21 and C27 are updated.
  - The Sources "still missing" list now shows the status of each of the five documents.
  - There's a new changelog row.
- Selfchecks pass.
- Still to do: C13 (CIO 2024–25) and C16 (senior-citizen circular). Both are scans and need `brew install poppler` to render the pages.
- **C34 added (Som's choice: keep the FY24 comparison as a separate news-sourced claim).**
  - The claim: "In 2023–24, insurers rejected about 11% of health claims and paid about 83%." Secondary, B3, IndiaMedToday. The care note says not to call the change a trend (prompt rule 6).
  - It's in `data/ledger.json`, both brief copies (a bullet after C10 plus a sources row) and the ledger doc (claim row, B3 in the bucket table, changelog row, count 33 → 34).
  - The brief's `brief_sha` changes again.
- Installed `poppler` (brew), so the scanned PDFs (C13, C16) can now be rendered for checking.
