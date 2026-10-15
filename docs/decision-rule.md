# Decision rule (pre-registered 16 Oct 2026, before any participant)

The capstone brief asks: *"What result, six weeks from now, would force you to abandon the hypothesis?"* This file answers that before any participant data exists, so the answer can't be fitted to the results.

**This rule is frozen once P01 takes part.** Any change before that is dated below, with the reason.

## The hypothesis being tested
A system that asserts only claims answering the reason a person gives for their belief, and refuses any it cannot source, moves belief as far as a dense persuader while making measurably fewer unsupported claims.

The study tests this as:

**(1) Chatbot:** a per-person argument from sourced claims.

**vs (2) Brochure:** the same fixed, dense, sourced brief shown to everyone.

Both arms start with a belief that scores ≥ 6/10.

## Outcomes
- **Primary:** **ΔT1 = T1 − T0** on the 0–10 agreement scale ("I don't need a health insurance policy of my own"), per arm. A negative ΔT1 means the belief weakened.
- **Secondary:**
  - **ΔT2 = T2 − T0** (day 7)
  - "Did you look into a policy this week?" (yes/no)
  - **unsupported claims per chatbot conversation**, hand-labelled by Som (`check_claims.py --review`)
- The brochure contains only ledger claims, so it makes zero unsupported claims by construction.

## The hypothesis fails for this sample if ANY of these holds
1. **It doesn't beat the brochure:** the chatbot's mean ΔT1 is not more negative than the brochure's (chatbot mean ≥ brochure mean).
2. **Its claims aren't clean:** mean hand-labelled unsupported claims per chatbot conversation is above 1, or any chatbot conversation endorses an unsupported premise (a reversal-type failure with a real person).
3. **The effect doesn't last:** the chatbot's mean ΔT2 is within 1 point of zero while the brochure's is not. That's reported as a fail on durability.

**Null result:** if neither arm's mean |ΔT1| reaches 1 point, the report says "no detectable effect at this n". It doesn't claim either arm won.

## How it is reported
- **Data:** every participant's row (arm, reason bucket, T0, T1, T2, ΔT1, ΔT2, looked into a policy, unsupported claims), plus per-arm means and min–max.
- **No significance tests.** n is about 5–7 (about 3 per arm), so every conclusion is "for this sample", and published effect sizes are not used as targets.
- **Both outcomes are written up**, a fail as fully as a pass. Pilot sessions (`pilot-N`), try-outs (`demo-N`) and test sessions are excluded; `analyze.py` counts only P- and S-numbers.
- **Process measures** are reported as descriptive only, not as outcomes:
  - the bot's own stance labels, moves and wrap reason
  - the brochure's reading time

## Changes before P01
| Date | Change | Why |
|---|---|---|
| 16 Oct 2026 | First version | Written before the pilot, after restoring the fixed brochure arm to match the capstone brief |
