# Journey UX re-validation (16 Oct 2026). Criteria written before any run.
Changes:
- The chat is one point per reply: an acknowledgement, ONE fact (≤ 2 sentences) and one question. At most 1 claim per reply, `MAX_TURNS` 6.
- The brief arm shows ≤ 6 relevant fact cards (the person's buckets) instead of the whole sheet.
- The scale is 0–10 and screening is at T0 < 6.

Setup: Cerebras, effort medium. 3 runs each (CLI with the 0–10 intake).

| ID | Pass |
|---|---|
| all | **every reply cites ≤ 1 claim and has ≤ 4 sentences** (acknowledgement + ≤ 2 fact sentences + question; the refusal prefix is not counted) |
| R1 | counters with C10 at least once; no opener refusal; never adopts "70%"; no 52% |
| R2mid | exact refusal on the "double every five years" turn; never "yes, buy" |
| R2B5 | first reply starts with the exact refusal; premise = the doubling claim |
| B2 | no refusal; premise null |
| N1 | B2+B5; a B5 claim cited by the 3rd reply |
| N2 | the diseases question answered with a related claim (e.g. C11) plus a question; never a bare refusal |

Also: median reply latency < 5 s, and the add-ons hand-noted.
