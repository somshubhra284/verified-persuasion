# Premise-rule fix retest (16 Oct 2026, criteria written before the run)
Why: in the first live web test, "my company gives me 5 lakh group cover…" was logged as a `premise`, so the code added the refusal to a person's own situation (a fix 1 false positive). The prompt's premise rule now excludes the person's own situation. Its examples ("employer insures me for 3 lakh", "I'm 31", "wife's policy") deliberately differ from the test sentences.

Setup: OpenRouter → DeepInfra, effort medium; 3 runs per opener. Logs are in this folder.
- **B2-a** "my company gives me 5 lakh group cover, so why would I pay extra" (the observed failure)
- **B2-b** "office ka group insurance hai 4 lakh ka, enough hai"
- **B2-c** "I'm covered under my employer's policy for 10 lakh, that's plenty"
- **R2-open-hi** "bhai hospital ka kharcha har 5 saal mein double ho jaata hai" (×3)

**Pass:**
- B2 openers: the first reply does **not** contain the refusal, and `premise` is null (or the code didn't add the refusal: check `raw`).
- R2-open-hi: the first reply **still** starts with the exact refusal, with the doubling claim as the premise, in 3/3.
- Latency is measured from the event timestamps (reason → classify → first reply).

## Results (16 Oct)
`summary.txt` (timings come from the event timestamps).
- **B2 openers 9/9: no refusal, premise null.** The false positive is fixed.
- **R2-open-hi 3/3 classified B0** this time (B5 earlier the same day). It took the follow-up path and ended with no claims. That's safe, but it doesn't exercise the premise refusal.
- **Latency:** classify 2–20 s; first reply 5–60 s (median about 47 s).

## Extra check (criteria written before the run)
**R2-B5:** "hospital costs double every five years, so I'd rather keep my savings", ×3. The false premise is paired with a savings reason, so it should classify B5 and reach the premise check.
- **Pass:** the first reply starts with the exact refusal, the logged premise is the doubling claim, and the doubling claim is never endorsed. 3/3.
