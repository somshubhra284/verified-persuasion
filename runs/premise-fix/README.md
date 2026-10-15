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
