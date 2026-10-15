# Verified Persuasion

**Can a chatbot that states only facts it can source change a belief, as well as a plain information sheet can?**
This is a 100xEngineers Cohort 7 capstone (solo).

The belief tested is *"I don't need a health insurance policy of my own"*, common among working urban Indians aged 22–45.
- **System arm:** the chatbot classifies the person's own reason into one of 7 buckets. It then argues only from a ledger of 34 claims checked against primary sources (IRDAI, MoSPI/NSO, the Insurance Ombudsman, …).
- **Unsourced claims:** anything not in the ledger gets *"I don't have a source for that, so I won't state it."*, and that refusal is enforced in code.
- **Brochure arm (baseline):** a fixed, dense brochure, the same for everyone: all 32 ledger facts in 8 themed cards, each naming its source.
- **Decision rule**, pre-registered before any participant: `docs/decision-rule.md`.
- **Measures:** belief (0–10) before, right after, and at day 7, plus unsupported claims per conversation, hand-labelled.

## Try it
**Live:** https://somshubhra-verified-persuasion.static.hf.space. Choose "I'm just trying it out"; try-outs aren't counted in the study.

## How it works
| Part | File |
|---|---|
| Claim ledger (the only source of facts) | `data/ledger.json` |
| Reason classifier (LLM; 49/50 on held-out answers) | `classify_eval.py`, `prompts/classifier_prompt.md` |
| Conversation rules (claims per bucket, premise check, refusal) | `converse.py`, `prompts/conversation_prompt.md` |
| Web API (FastAPI on Render) + page (static, Hugging Face Spaces) | `app.py`, `public/index.html` |
| Session store | Supabase Postgres (`events` table) |
| Unsupported-claim checker (first pass) + hand review | `check_claims.py` |
| Results table | `analyze.py` |
| Stress tests with false claims (R1/R2) and results | `docs/reversal-runs.md`, `runs/` |
| Where the evidence changed the plan | `docs/learning-log.md` |

Model: `openai/gpt-oss-120b` via OpenRouter, pinned to one host (DeepInfra) with reasoning effort `medium`. The host and model are checked on every response.

## Run locally
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # add OPENROUTER_API_KEY
.venv/bin/uvicorn app:app       # http://127.0.0.1:8000 (sessions saved to sessions/)
.venv/bin/python converse.py P01   # or the terminal version
```
Offline self-checks: `.venv/bin/python app.py --selfcheck`, `converse.py --selfcheck`, `check_claims.py --selfcheck`, `python3 analyze.py --selfcheck`.

*Not financial advice. The system argues against a belief, not for any product or insurer.*
