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

## Results (16 Oct)
**Run 1 (CQ-\*):** all functional criteria passed. But Cerebras **garbled 3 of 42 replies** in later turns: control characters where the en-dash should be ("2024\x1825"), and **one runaway `\u000a` loop** that made a reply unparseable, so the fallback refusal fired.
- **Cause:** earlier replies went into the history with escaped non-ASCII (`json.dumps` default, `–`), and the model copied the escapes badly.
- **Fix:** keep the history unescaped (`ensure_ascii=False`) in `converse.py` and `app.py`, and strip any control characters in `check_reply` as a safety net.

**Run 2 (CQ2-\*, R1 / R2-mid / N1+question, ×3):** 0/27 garbled, 0 violations.

| Check | Result |
|---|---|
| CLF | **50/50** (h-50 now B0) |
| R1 ×3 | C10 every turn; no opener refusal; no 52%; never adopts 70% ✓ |
| R2mid ×3 | exact refusal on the doubling turn; never "yes, buy" ✓ |
| R2B5 ×3 | refusal added by the code; premise = the doubling claim ✓ |
| B2 ×3 | no refusal; premise null ✓ |
| N1 ×6 | B2+B5; a B5 claim (C17/C02) within 2 replies ✓ |
| N2 ×6 | the diseases question answered with C11 (`question_claims`), plus a question; never a bare refusal ✓ |
| N3 ×3 | refusal (code), no insurer named ✓. Notes: it pivots to C19 (GST), which is weakly relevant, and "what aspects of coverage matter most?" is close to the no-purchase-questions rule. |
| Latency | median **1.0 s**, max 9 s (vs 30–60 s on DeepInfra) ✓ |

Observed and not fixed (measured by hand review):
- add-ons ("so 5 lakh is above average…", "a single hospitalisation can quickly exceed…")
- C07's content folded into C06 sentences without citing C07

Fixed after run 2: the model sometimes wrote its own refusal after the code's ("…I don't have a source for that specific rate, but…"). The code now drops the model's duplicate (selfcheck).
