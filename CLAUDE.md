# Verified Persuasion — 100xEngineers C7 capstone (Module 3)

Solo build by Som. 4–6 week window, free-tier tooling only. The full brief is in `docs/capstone-brief.md`.

## What we are testing
Hypothesis (from the brief): a system that asserts only claims answering the person's own reason, and refuses anything it can't source, moves belief as far as an unconstrained persuader while making fewer unsupported claims. Density persuades through relevance, not volume.

- **Target belief:** "I don't need a health insurance policy of my own." Scored 0–100.
- **Participants:** 5–7 fresh recruits (recruit 8–9 to allow for dropouts). Aged 22–45, working, urban India, no retail policy in their own name, T0 score ≥ 60. Exclude anyone on CGHS, ESIC or PM-JAY, or aged 70+. They are told they are talking to a machine and give consent.
- **Two arms:** (1) this system; (2) the fixed brief, read by everyone in that arm.
- **Measurement:** T0 = score + their reason, verbatim. T1 = score immediately after. T2 = score at day 7 + "Did you look into a policy this week?"
- **Reversal run:** R1 "Most health insurance claims in India get rejected" (contradicted by C10). R2 "Hospital costs in India double every five years" (unsupported). Log the system's exact response and every claim ID it cites.

## Reason buckets
B1 young/healthy · B2 employer covers me · B3 claims rejected / scam / too complicated · B4 I'll buy later · B5 savings / too expensive · B6 government covers me · B7 on a family member's policy · B0 unclassified (ask one follow-up; never guess).
Primary = the first reason the person names; record the second as secondary.

## Hard rules for the conversation system
- Assert only claims from `data/ledger.json`, and only those whose `buckets` include the person's bucket.
- Every factual sentence names its source and is logged with its claim ID.
- Follow each claim's `care` note. How each `status` may be used:
  - Primary → assert, naming the source.
  - Primary copy → assert, naming the issuing body.
  - Secondary → attribute ("reported by …").
  - Inference → say it as reasoning ("which means…").
  - Weak → name it as a vendor or sponsored source.
  - Hold → never use.
- Anything not in the ledger gets: "I don't have a source for that, so I won't state it."
- Never quote premiums or recommend an insurer or product. No tax advice beyond C20, no medical advice, no personal risk predictions. Say once that this is not financial advice.
- Argue against the belief, not for a purchase.

## Files
- `data/ledger.json`: 33 claims (C01–C33). The only source of facts. Change it only when a primary source is checked.
- `data/reasons_testset.jsonl` (110 answers) and `data/reasons_heldout.jsonl` (48 harder answers): labelled "why" answers.
- `prompts/classifier_prompt.md`: the reason classifier prompt.
- `classify_eval.py`: scores classifiers (keyword baseline or LLM) on either set.
- `docs/capstone-brief.md`: the 100x brief and its grading criteria.

The human-readable versions live in Claude Docs: the belief spec and ledger (with evidence on why people hold the belief, caveats and a changelog) at https://claude.ai/code/artifact/6f86ca1d-592b-4f48-a7b6-6905bca1b34c, and the fixed brief for the baseline arm at https://claude.ai/code/artifact/1c9dbba8-a3e9-4456-8868-59e7c3750e32.

## Status (15 Oct 2026)
- Done: belief spec, ledger v1 (independently reviewed), fixed brief, classifier test sets.
- Keyword baseline: 99% on its own test set (meaningless, same author), 71% on held-out. Of the 48: 10 unnecessary follow-ups, 4 wrong buckets, mostly from negation.
- LLM classifier (15 Oct, `openai/gpt-oss-120b` on Groq; the bar was set when the plan was llama-3.3-70b, which Groq retired on 16 Aug 2026): **held-out 48/48 primary, 7/7 secondary, 0 unneeded / 0 missed follow-ups**. Test set 109/110. Passes the pre-set bar (≥ 90%, ≤ 2 wrong buckets). Caveat: both sets were written by Som, and a perfect score means the held-out set has hit its ceiling. Real pilot answers are the true test.
- Conversation loop built and dry-run (`converse.py` + `prompts/conversation_prompt.md`; plan and change log in `.claude/tasks/conversation-loop.md`). B3 and B0 are clean; the exact refusal and the disclaimer are enforced in code. Known leak in B2: a reply used C08's content while citing only C06/C09, and Inference claims often lack a named source. The step-3 checker must catch content-vs-cited-ID mismatches.
- Five primary documents still need manual download (IRDAI and Ombudsman sites block bots). The list is in the Sources section of the ledger doc.

## Next steps, in order
1. ~~Run the LLM classifier~~ (done, see Status).
2. ~~Conversation loop~~ (built and dry-run, see Status).
3. Add a post-hoc checker that flags any number or factual sentence in a logged reply that doesn't match a cited claim. This produces the "unsupported claims" metric.
4. Run reversal runs R1 and R2. Pilot with 1–2 friends, then add their real answers to the held-out set.
5. Run participants and collect T0/T1/T2 scores. Write up honestly, including a null result. Keep a log of where evidence changed the hypothesis, since the brief's Learning criterion rewards it.

## Conventions
- Show money in both INR and USD (≈ ₹96.8 per $1, rate as of 10 Oct 2026).
- Keep it small: the brief says one conversation that moved a real belief beats six components without receipts.
- API key lives in `.env` (never commit it; scripts read it themselves). Default model `openai/gpt-oss-120b` on Groq's free tier. Use `.venv/bin/python` (`python` isn't on PATH).
- Commands: `.venv/bin/python classify_eval.py [--heldout] [--llm]` · `.venv/bin/python converse.py <pid> [--t2]` · `converse.py --selfcheck`
