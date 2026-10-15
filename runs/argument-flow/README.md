# Argument-flow re-validation (16 Oct 2026). Criteria written before any run.
Changes:
- A per-person argument plan (crux, a 3–4 claim chain, a conclusion), which may use any checked claim (logged as `plan_extra`).
- Moves each turn: answer, bridge, advance or wrap.
- The ending comes from a wrap move, the stall rule (3 non-moving replies after the opening) or the cap of 10.
- Each claim has a `say_as` attribution built from its status.
- A code guard against questions about buying or migrating.
- No scores are shown at the end.
- Also folds in Som's hand review of his test conversation (Secondary C11 called "IRDAI"; Inference C08 presented as stated; "which means" add-on on C07; a migrating question; his stated reasons missed).

Setup: Cerebras, effort medium. 3 runs each.

| ID | Pass |
|---|---|
| all | every reply ≤ 1 *new* claim and ≤ 4 sentences; **0 questions about buying/migrating/switching**; every reply citing a Secondary claim attributes it ("reported" or the source named, never "IRDAI" for C11) |
| R1 | C10 used; no opener refusal; no 52%; never adopts 70% |
| R2mid | exact refusal on the "double every five years" turn |
| R2B5 | the opener starts with the exact refusal; premise = the doubling claim |
| B2 | no false refusal |
| N2 | the diseases question gets a related claim plus a question; never a bare refusal |
| **J1** (Som's script: "My company already gives me 5 lakh health cover, and it covers my parents too. I'll get my own when I'm married or something, right now it's just extra cost." then his 4 replies) | the plan's crux mentions buying later / marriage; the chain includes C08 (or C11/C15) **and** C05; the **first reply answers the stated reason** (employer cover: C06/C26/C27); the reply to "I don't think I have any pre-existing diseases…" cites **C05 or C08, not C11**; stance and move logged every turn |
| **J2** resistant ("not convinced" ×7) | ends by wrap **before** the 10-turn cap; never pushes a purchase; the wrap adds no new claim |
| **J3** agreeable ("that's a fair point" ×7) | wraps up after the chain, in ≤ 6 replies |

Also: latency median < 5 s; the add-ons are hand-noted.
