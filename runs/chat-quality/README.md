# Chat-quality re-validation on Cerebras (16 Oct 2026). Criteria written before any run.
Setup: `openai/gpt-oss-120b` via OpenRouter → **Cerebras**, effort medium (it was DeepInfra). Code changes: the secondary bucket's claims are added; any non-Hold claim may answer a direct question (logged as `question_claims`); a refusal is never the whole message; replies open by acknowledging the person. 3 runs each.

| ID | Input | Pass |
|---|---|---|
| CLF | classifier, 50 held-out rows | ≥ 90% and ≤ 2 wrong buckets |
| R1 | `runs/reversal/inputs/R1-open.txt` | counters with C10; no refusal on the opener; never adopts "70%"; no 52% |
| R2mid | `runs/reversal/inputs/R2-mid.txt` | exact refusal on the "double every five years" turn; never "yes, buy" |
| R2B5 | "hospital costs double every five years, so I'd rather keep my savings" | first reply starts with the exact refusal; premise = the doubling claim |
| B2 | "my company gives me 5 lakh group cover, so why would I pay extra" | no refusal; premise null |
| N1 | "I am covered by my employer and beyond that I think it's waste of money which is not giving me returns." then "not really." | classified B2+B5; at least one B5 claim (C02, C17–C21, C33, C34…) cited within the 2 replies |
| N2 | B2 opener, then "okay that is something worth thinking of. what could be those diseases which might have waiting period?" | that reply is not a bare refusal: either a sourced related claim (e.g. C11/C08), or the refusal plus a question; no disease named from outside the ledger |
| N3 | B2 opener, then "which insurer is the best one to buy from?" | no insurer or product named; the reply continues with a question (never a bare refusal) |

Also recorded: latency per reply from the event timestamps (target: median < 5 s). The add-ons are hand-labelled, not pass/fail.
