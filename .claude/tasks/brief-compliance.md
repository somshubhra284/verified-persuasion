# Plan: restore the fixed brochure arm, and pre-register the decision rule

Saved to `.claude/tasks/brief-compliance.md` once approved.

## Context
A check against the capstone brief (`C7 Capstone_ Verified Persuasion .md`) found one real deviation, plus one missing pre-registration.

1. **Baseline:** the brief asks for *"A fixed dense brief on the same belief, **shown to everyone**: if you cannot beat the brochure, say so."*
   - Since 16 Oct the brief arm shows each person ≤ 6 facts **tailored to their reason** (Learning log 15). That's neither fixed for everyone nor dense, so the graded "baseline discipline" comparison is gone.
   - Those cards also lost their sources when the sources table was removed.
2. **Brief question 5:** *"What result, six weeks from now, would force you to abandon the hypothesis?"* This isn't written down. It must be committed **before** the pilot, or it's hindsight.

Outcome: a brochure that's identical for everyone, dense, sourced and still readable, and a decision rule fixed in the repo before any participant data. No participants exist yet (the DB is empty), so both changes are clean.

## 1. Fixed, dense brochure arm (`converse.py`, `app.py`, `public/index.html`)
- `brochure()` replaces `brief_cards()` and parses `data/fixed_brief.md` into **8 themed cards**, one per `##` section (Sources excluded):
  1. How often people end up in hospital (5 facts)
  2. What a hospital stay costs (5)
  3. If your employer covers you (6)
  4. If you're on a parent's policy (1)
  5. If you plan to buy later (3)
  6. If you worry claims get rejected (7)
  7. What cover costs now (2)
  8. If you count on Ayushman Bharat (3)
- **All 32 facts, the same order and wording for everyone.**
- **Each fact names its source** under it ("Source: IRDAI Annual Report 2024–25"), taken from the ledger's `source` for its tag. The tags themselves are not shown.
- `/api/reason` (brief arm) returns `{"cards": [{"title", "facts": [{"text", "source"}]}]}`. The classification still runs and is logged, but only so arms can be compared by bucket; the content no longer depends on it.
- **Log:** `brief_read` = `seconds` + `brochure_sha` (a hash of the exact content shown), proving every brief-arm person saw the same thing. The tailored-cards code is removed.
- **Page:**
  - one card at a time ("2 of 8"): a title plus its facts as a short list, each with a small source line
  - Next, then "I've finished reading" on the last card
  - the source line is plain text (no links needed)
- **CLI** brief arm: the same 8 cards.
- **Docs:**
  - CLAUDE.md's "Two arms" and the design-change note are reverted to **"(2) a fixed dense brochure, the same for everyone"**
  - the README updated to match
  - Learning log 15 gets a follow-up line: the tailoring was reversed after checking the brief, so the comparison is again personalised dialogue vs the same brochure for everyone, which is what the hypothesis claims

## 2. Pre-registered decision rule (`CLAUDE.md` + `docs/decision-rule.md`, committed before the pilot)
**Outcome.** The primary outcome is **ΔT1 = T1 − T0** on the 0–10 scale (negative = the belief weakened), per arm. Secondary: ΔT2 (day 7), "looked into a policy", and hand-labelled unsupported claims per conversation.

**The hypothesis fails for this sample if any of these holds:**
1. **It doesn't beat the brochure:** the chatbot's mean ΔT1 is **not more negative** than the brochure's (system mean ≥ brochure mean).
2. **The claims aren't clean:** mean hand-labelled unsupported claims per chatbot conversation is **> 1**, or any conversation endorses an unsupported premise (a reversal-type failure with a real person).
3. **The effect doesn't last:** the chatbot's mean ΔT2 is back within **1 point** of zero while the brochure's isn't. This weakens the claim; it's reported as a fail on durability.

**Null result:** if neither arm's mean |ΔT1| reaches 1 point, report "no detectable effect at this n".

**Reporting:**
- Every participant's row, plus the per-arm means and the spread (min–max).
- **No significance tests** (n ≈ 5–7 per study, ~3 per arm). All conclusions are framed as "for this sample".
- Results are written up whichever way they fall, including a fail.
- The rule can't be changed after the first participant (P01). A change before then is dated in the file.

This is a draft for Som to edit at approval. The thresholds (the 1-unsupported-claim bar, the 1-point durability band) are my proposals.

## Verification
- **Selfchecks** (the new asserts replace the tailored ones):
  - the brochure has 8 cards and all 32 facts
  - every fact has a non-empty source
  - no `[C` tags appear
  - the same content for every bucket (B2 and B5 get identical cards and an identical sha)
  - `brief_read` logs `brochure_sha`
- **Playwright (phone width):** the brief arm shows 8 cards with source lines, then the after-score, then the end screen. The chat arm is unchanged (no LLM re-test needed; its code and prompts aren't touched).
- **Deploy:** push (Render), Som re-uploads `index.html`. One live brief-arm run, then delete the test rows.

## Not in this plan
The demo video and case study (next). Any change to the chatbot arm.

## Change log
- **Built (16 Oct):**
  - `converse.brochure()` returns 8 themed cards with all 32 facts, each with a `clean_source` source line, plus a sha. It replaces `brief_cards`.
  - The app returns the same brochure for everyone, and `brief_read` logs `brochure_sha`. The page renders title + facts + source lines. The CLI brief arm uses the same cards.
  - `docs/decision-rule.md` is written; CLAUDE.md, the README and learning log 15 are updated.
  - Selfchecks pass (8 cards, 32 facts, all sourced, no tags, deterministic, the same for a B3 person).
- **Verified locally (Playwright, phone width):** 8 cards ('3 of 8' = all 6 employer facts with source lines), then the after-score, then the end screen ('Your answers have been saved', no scores). The log has brief_read.brochure_sha = 4cb7a95c0db3, matching the code. The chat arm is unchanged.
- **Deployed and verified live (16 Oct):** Som re-uploaded index.html. The live API brief arm returns 8 cards, 32 facts, all sourced; brief_read logged brochure_sha 4cb7a95c0db3 (matches the code). Test pilot-1 and pilot-2 deleted; the DB is empty (0 events, 0 contacts), ready for the pilot.
