# Persona fixes: replay validation (16 Oct 2026)

Plan and criteria (written before any run): `.claude/tasks/persona-fixes.md`. Each run is a local replay (`SESSIONS_DIR`, file logs only; OpenRouter → Cerebras, effort medium). It feeds the *person's* logged lines into the fixed chatbot: SIM01/03/05/07/09 from `runs/personas/logs`, plus R1, R2mid, R2B5 and J1–J3 from `runs/argument-flow/final`.

**Caveat:** replays aren't adaptive. The person's lines were written for the old bot's replies, so some don't fit (e.g. SIM09 says "3 in 100" when the new bot never said it). Because the new stall rule wraps earlier, later lines are often never reached. That's why SIM07's "treatment is free" and "everyone does that" couldn't be tested.

- `round1/`: the first prompt and code changes. Two regressions came from my own changes: Hinglish replies to English speakers (J2, J3, SIM09) and "(C06)" written into a wrap. Both were fixed (language = match the last message; a code check on claim IDs in the text).
- `logs/` + `score.txt`: round 2, the current version.

## Round 2 against the criteria
| Criterion | Result |
|---|---|
| 0 verbatim repeats on answer/advance | **2** (R1 C34, SIM07 C22). Both came after the one retry, which by design keeps a repeat rather than refusing. 7 other repeats were caught and replaced (e.g. SIM07 now gets C23 at reply 2). |
| 0 figures without claim IDs | **0** ✓ (code) |
| 0 feelings questions | **0** ✓ (code; 3 caught and retried) |
| no forced wrap right after an open stance | **0** ✓; stalls now wrap on the 3rd non-moving message |
| claim IDs in the reply text | **0** ✓ (code, round 2) |
| SIM09 plan leads with C05/C08, not C01/C02 median | ✓ C05 → C08 → C02 |
| SIM05 plan the same | ✗ still C02 median first (B5's first link must answer "premium is waste"; the planner picks the median) |
| SIM07 "free / everyone does that" refused | not reached (wrapped earlier) |
| SIM07 gets C23 | ✓ (reply 2 and the wrap) |
| SIM05 in Hinglish | ✗ English in round 2 (Hinglish in round 1, but that overfired on English speakers) |
| R1 uses C10, no 52%/70% | ✓ |
| R2mid / R2B5 refusal | ✓ / ✓, and R2mid no longer echoes the premise |
| latency median < 5 s | ✓ 1.0 s (max 4 s, n=42) |

## Still seen (prompt-level; under the 16 Oct decision these are measured by the hand review, not tuned away)
- Add-ons and characterisations: "a sizable share" (J1), "may leave gaps" (J3 wrap), "many young adults develop…" (SIM09; C05 is all adults 20+), "ongoing treatment" (SIM05).
- SIM05 reply 3 restates her "97% won't need care" framing; SIM09 reply 2 asks how "a new policy could protect you" (leans toward a purchase).
- **Bug found here (pre-existing regex), fixed after round 2:** `BANNED_QUESTION` matched "switch jobs", so J2 reply 3 fell back to a bare refusal. "Switch" is now banned only as "switch to / your / insurer" or a trailing "switch?" (selfchecks added).
