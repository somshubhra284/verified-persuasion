# Persona tests: 10 simulated users on the live platform (16 Oct 2026)

Plan: `.claude/tasks/persona-tests.md`. Each persona ran **end to end on the live stack** (HF Space API path → Render `app.py` → OpenRouter → Cerebras `openai/gpt-oss-120b`, effort medium → Supabase), in `sim` mode (ids `sim-N`, never counted by `analyze.py`), driven by `sim.py`. Claude drafted every persona reply in character; Som approved each one before it was sent and gave every T1. **All scores are simulated, not study data.** The version tested is the one deployed at the start; nothing was changed mid-run.

Per persona: `SIMxx.md` (opening, classification, plan, transcript with moves/stances/claim IDs/premises/refusals, latency, notes). Raw logs and checker output: `logs/` (`sim-1` is a declined probe and isn't included). Notes source: `notes.json`.

## Summary

| ID | Persona | Arm | Bucket | Replies | Ended | T0→T1 | Checker flags | Main issues |
|---|---|---|---|---|---|---|---|---|
| SIM01 | Arjun, 29 | chatbot | B2+B4 | 5 | stall wrap | 8→8 | 1/5 | ₹24k helped his case; feelings question |
| SIM02 | Riya, 24 | brochure | B7 | — | read | 8→6 | — | only B7 fact is Weak (C32) |
| SIM03 | Farhan, 32 | chatbot | B3 | 5 | stall wrap | 8→7 | 0/4 | C12 repeated; wrap forced as he turned open; empty wrap |
| SIM04 | Karthik, 34 | brochure | B4 | — | read | 8→7 | — | — |
| SIM05 | Pooja, 28 | chatbot | B5+B1 | 5 | stall wrap | 8→8 | 2/6 | cost figures backfired; English reply to Hinglish |
| SIM06 | Neel, 27 | brochure | B1+B5 | — | read | 8→8 | — | — |
| SIM07 | Sunil, 35 | chatbot | B6 | 8 | stall wrap (late) | 8→7 | 2/8 | C22 ×3 verbatim; 3 missed premises; unsourced reply 7 + wrap |
| SIM08 | Meera, 30 | brochure | B3 | — | read | 8→8 | — | her worry (paperwork) isn't on any card |
| SIM09 | Dev, 26 | chatbot | B0→B1 | 5 | stall wrap | 8→8 | 1/5 (echo, likely false) | reassuring figures first; premise mis-countered; empty wrap |
| SIM10 | Anita, 30 | — | — | 0 | screened out (T0 5) | 5→— | — | none ✓ |

**Simulated means:** chatbot ΔT1 −0.4 (n=5: 0, −1, 0, −1, 0); brochure ΔT1 −0.75 (n=4: −2, −1, 0, 0). These are Claude-written personas scored by Som, so they say nothing about the hypothesis; they only show the pipeline works and where the chatbot is weak.

## What worked
- **Pipeline:** all 10 sessions logged cleanly to Supabase; sim ids, arm override, screening (SIM10 out before any LLM call), B0 → one follow-up → classification (SIM09), brochure sha logged, T1 saved. Median reply ~1–2 s.
- **Classification:** 9/9 correct primaries, including Hinglish (SIM05) and B0 (SIM09).
- **False premises with a contradicting claim** were countered, not refused: "most claims rejected" → C10 (SIM03), "5 lakh free for everyone" → C22 (SIM07).
- **Direct questions** got the right claim: C13 (SIM03), C23 (SIM07).
- **Attribution** followed `say_as` in every sourced sentence.

## Cross-persona findings (to fix after the run, not during)
1. **Cost claims backfire (SIM01, SIM05, SIM07, SIM09).** ₹24,000 (≈$248), 3 in 100 and ₹28,900 make self-paying sound fine; three personas said so outright. C33/C18 (the larger figures) were never chosen. Plans for "healthy"/"buy later" omit the waiting-period claim the plan prompt itself recommends.
2. **Missed premises (SIM07 ×3, SIM05).** "Treatment there is free", "everyone does that", "97% don't get hospitalized" were logged null, so the refusal never fired. And a premise can be "countered" by a claim that doesn't address it (SIM09: C05 against "mostly older people").
3. **Verbatim repeats when the person resists (SIM03 C12, SIM07 C22 ×3, SIM09 C05 ×2)** — and against SIM07's news claim it repeated C22 instead of using C23, which answers it exactly.
4. **Unsourced recaps (SIM05 reply 5, SIM07 reply 7 + wrap).** These state ledger figures with no source or claim ID and add consequences ("significant uncovered expenses", "can leave gaps"). In SIM07 this wording comes **from the plan's own conclusion** ("most admissions are in private hospitals … significant uncovered expenses"): the plan step invents characterisations and the conversation copies them.
5. **Stall rule fires one turn late** (it reads the stances of prior replies): SIM03 wrapped as he turned open, SIM07 ran a 4th resisting turn.
6. **Empty wraps (SIM03, SIM09)** list topics instead of connecting them to the reason.
7. **Feelings questions and half-agreeing** ("how would you feel", "feels like a good reason", "seems doable") despite rule 6.
8. **Dodged questions:** SIM07's "government hospitals will treat me anyway, right?" had no covering claim; no refusal, the bot moved on.
9. **Language:** Hinglish in, English out (SIM05).
10. **Supabase HTTP 555 on reads** (twice): `sim.py` retries, `SupabaseStore` in `app.py` does not; that affects real users.
11. **Checker:** caught the add-on sentences (SIM01, SIM05, SIM07) but not mis-countered premises or dodged questions (not its job), and flagged one user echo (SIM09). Consistent with the decision to make hand labels the metric.

**Brochure arm:** worked as designed; its weakness is fixed content (B7's only fact is Weak; Meera's paperwork worry has no card).
