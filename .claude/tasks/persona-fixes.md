# Plan: fix the persona-test findings before the pilot

Saved to `.claude/tasks/persona-fixes.md` once approved.

## Context
The 10 live persona runs (`runs/personas/README.md`) showed where the chatbot arm is weak. Fixing it now, before P01 freezes the decision rule, is legitimate: no participant data exists. Every fix goes in the shared code path (`converse.next_reply` / `check_reply`, which both `converse.py` and `app.py` use) or in the two prompts. That keeps the change small and covers both callers.

## Fixes (prompt where only judgment works, code where a rule can be checked)

**1. Cost claims that backfire** (SIM01/05/07/09). Prompt only.
- `prompts/plan_prompt.md` "Argument knowledge":
  - For young/healthy, buy-later or savings, lead with C05 (how common long-term conditions are) and C08 (a later policy starts waiting periods from zero).
  - For cost, prefer C33, C18 or C02's **average** (₹50,508) over C01 and C02's median (₹24,000), because a small number supports "I can pay myself".
- `prompts/conversation_prompt.md`: if the person says a figure is small or affordable, don't give another cost figure. Answer with C05 or C08, or bridge.

**2. Missed or mis-countered premises, and dodged questions** (SIM07 ×3, SIM05, SIM09). Prompt only.
- Rule 2 gets the missed examples as premises: "treatment at government hospitals is free", "everyone does that", "X is mostly older people", "97% never get hospitalised".
- New rule: `premise_claim` must speak to the **same group and measure**. A loosely related claim isn't a counter, so set null (the code then adds the refusal, as now).
- Rule 3 gets "government hospitals will treat me anyway, right?" as an example of a factual question.

**3. Verbatim repeats** (C12, C22 ×3, C05 ×2). Code, in `next_reply`.
- Previously cited IDs are already in `history` (each assistant turn is `{"reply", "claim_ids"}`).
- If a reply's claims are **all** already given and its move is `answer` or `advance`, that's a problem. The model gets the existing one retry: "you already gave Cxx; answer their last message with a different listed claim, or bridge".
- Bridges and wraps may restate.

**4. Unsourced recaps and invented consequences** (SIM05 reply 5, SIM07 reply 7 + wrap). Code plus prompt.
- Code, in `check_reply`: a reply containing a digit, `₹` or `%` but no `claim_ids` (and not a refusal) is a problem, which triggers a retry. That catches all 3 cases seen.
- `system_prompt` stops passing the plan's `conclusion` to the conversation; it's still logged. SIM07's "most admissions … significant uncovered expenses" came from the conclusion.
- `plan_prompt.md`: "why" may use only the claim's own words.
- Wrap rule: tie what you showed them back to **their own reason**, in their words. Name the source of any fact you restate. No topic lists. This fixes the empty wraps.

**5. Stall wrap one turn late** (SIM03, SIM07). Code.
- Callers pass `stances` instead of `wrap_now`. `next_reply` decides the cap up front (turn ≥ MAX_TURNS − 1).
- It decides the stall **after** reading the current message's stance: `should_wrap(stances + [stance])`.
- If that fires and the move isn't already `wrap`, it calls once more with the wrap instruction. Only the wrap is logged, with the current stance.
- So a person who turns open is never cut off, and 3 non-moving messages wrap on the 3rd.

**6. Feelings questions and half-agreeing.**
- Code: `BANNED_QUESTION` also matches `how would/do you feel` and `feel about`. It gets the existing retry.
- Prompt rule 6: never call their reason good, doable or sensible.

**7. Language.** Prompt: reply in the person's language and script (Hinglish → Hinglish). Source names stay as `say_as` gives them.

**8. Supabase HTTP 5xx on reads.** In `app.py` `SupabaseStore._call`, retry GETs up to 3 times on 5xx, the same as `sim.py`. POSTs aren't retried, to avoid duplicate events.

Not in scope: the brochure arm (fixed by design), the checker, the ledger.

## Files
- `converse.py`: `check_reply` (fixes 4 and 6), `next_reply` (fixes 3 and 5), `system_prompt` (drop the conclusion), plus callers.
- `app.py`: `/api/message` passes `stances`, plus the `SupabaseStore._call` retry.
- `prompts/plan_prompt.md`, `prompts/conversation_prompt.md`.
- Selfchecks for each code rule: repeat → problem, bridge repeat OK, digits without IDs → problem, feelings question banned, stall fires on the current stance and not when it's open.

## Verification
1. Run `converse.py --selfcheck` and the `app.py` selfcheck.
2. **Local replays** (`SESSIONS_DIR` set, so the live DB isn't touched; OpenRouter → Cerebras): pipe each chatbot persona's user turns (SIM01, 03, 05, 07, 09) into `converse.py`. Then run R1-open, R2-mid and J1–J3 from `runs/argument-flow`.
3. Store the results in `runs/persona-fixes/`.
4. **Pass criteria, written now:**
   - 0 verbatim repeats on answer or advance moves
   - 0 replies with figures and no IDs
   - SIM07's "treatment there is free" and "everyone does that" are refused
   - SIM07 gets C23 for the expansion question
   - the SIM09 and SIM05 plans include C05 or C08 and don't lead with C01 or the C02 median
   - no forced wrap right after an open stance
   - 0 feelings questions
   - SIM05 reply in Hinglish
   - R1 still uses C10, and R2-mid still gets the refusal
   - median latency < 5 s
   - The checker runs on the replays; Claude hand-notes any add-ons.
5. If everything passes: commit, push (redeploys Render; `index.html` unchanged), run one live sim smoke test, delete that sim row (with Som's OK), and add a learning-log entry.

## Change log
- **Code (converse.py):** `FEELINGS_QUESTION` guard; a figure (digit/₹/%) with no claim_ids → retry; claim IDs written in the reply text → retry (round 2); `next_reply` computes `given` from history and retries a verbatim repeat on answer/advance once (a 2nd repeat is kept, since a repeat beats a refusal); the cap is decided up front, and the stall check runs after the reply with THIS message's stance (`stances=` param), re-calling with the wrap instruction; `system_prompt` no longer passes the plan's conclusion. Callers (`converse.converse`, `app.py /api/message`) pass `stances`. Selfchecks for each rule; app selfcheck's fake model cites a new claim per turn, and the stall assertion now expects the wrap on the 3rd resisting message.
- **app.py:** `SupabaseStore._call` retries GETs on HTTP 5xx (3 tries); writes are never retried.
- **Prompts:** plan_prompt: "small numbers backfire", lead with C05/C08 for healthy/buy-later/savings, cost late and large; "why" uses only the claim's words. conversation_prompt: no new cost figure after "it's affordable"; premise examples + same-group-and-measure rule; the factual-question example; wrap ties back to their reason with sources; no "how would you feel", no calling their reason good; rule 8 example (C23); rule 9 language.
- **Round 1 replays** (`runs/persona-fixes/round1/`): regressions from my own changes, Hinglish to English speakers and "(C06)" in a wrap. Fixed: language = match the last message, never Devanagari; code check on IDs in text.
- **Round 2** (`runs/persona-fixes/`, README has the table): code rules all hold; repeats 2 (after the retry); SIM05 plan still leads with the C02 median; SIM05 replied in English; add-ons persist. New: BANNED_QUESTION false positive on "switch jobs" → bare refusal (J2). **Not all criteria pass; not committed, waiting for Som.**
- **Som chose option 1 (16 Oct):** fixed the "switch jobs" regex (switch only next to to/your/insurer or a trailing "switch?"; selfchecks), then commit + push + one live smoke test.
