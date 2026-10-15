# Plan: an argument that progresses (plan → adaptive moves → natural end)

Saved to `.claude/tasks/argument-flow.md` once approved.

## Context
Som's test conversation (P03, screenshot of 16 Oct) showed facts without a destination.
- The bot answered each message with the next fact from the primary bucket (B2).
- It never named the real crux, "I'll buy when I'm married" (B4).
- It ignored a disengaging "can't imagine why that matters".
- It answered "I have no pre-existing diseases" with an unrelated waiting-period cap, when the persuasive reply was C05 (1 in 9 adults has diabetes) linked to C08 (a later policy restarts waiting periods).
- The turn count was fixed at 6, with no sense of progress.

Decisions (Som, 16 Oct):
- Build a per-person argument plan.
- Adapt each turn to how the person responds.
- End when the argument has landed or stalled, not at a fixed count.
- **C05-style links (a):** the plan may use any checked, non-Hold claim that fits the person's crux. It's logged, like question answers are.
- **End screen:** don't show the user their scores. Record them only (the case study uses them).
- Keep the workflow's approval step, and re-test the safety checks.

## Changes
### 1. Argument plan at the start (`converse.py`, new `prompts/plan_prompt.md`)
- `make_plan(client, model, reason, primary, secondary)` makes one LLM call (JSON mode, the same pinned host and effort). It's given the person's words, their buckets, and all usable claims (id, claim, figure, source, status, care). It returns:
  `{"crux": "<their underlying belief, one line>", "chain": [{"claim_id": "C06", "why": "<how this fact bears on the crux, from the claim's own content>"}, …3–4], "conclusion": "<the point the chain builds to, without new facts>"}`
- **Code validation:**
  - It keeps only usable (non-Hold) IDs, with no duplicates, and at most 4.
  - On a parse failure or an empty chain, it falls back to the first 3 claims from `reason_claims([primary, secondary])`.
  - It's logged as a `plan` event (crux, chain, conclusion, and `plan_extra` = chain IDs outside the person's buckets, the C05 case).
- **Allowed claims for reasons** = bucket claims ∪ plan chain. Anything else is used only for a direct question (`question_claims`, unchanged).

### 2. Adaptive moves + progress signal (`prompts/conversation_prompt.md`, `converse.py`)
- The prompt gets the plan. Each turn the model first reads the person's last message, then picks ONE move:
  - **answer:** they raised a new point or question. Answer that point with the most relevant claim (from the plan, else any usable claim if they asked directly).
  - **bridge:** they're resisting, disengaging, or don't see why it matters. Connect the last fact to *their own words and plan* ("You mentioned marriage…"), restating a claim's content only. No new facts and no personal risk prediction.
  - **advance:** they're open or neutral. Give the next chain link.
  - **wrap:** the chain has landed and they're open, OR there's been no movement for 2 turns. In 1–2 sentences, connect what was shown (only claim content already used) and thank them.
- Still one fact per reply at most (a bridge or wrap may restate, never add). Questions are about their *reasoning*, never feelings or buying.
- **New JSON fields:** `stance` (agrees/open/neutral/resisting/disengaged), `move` (answer/bridge/advance/wrap), `new_point` (text or null). Logged on each assistant event.
- **Ending, in code:**
  - The conversation ends after a `wrap` reply.
  - If the last 3 stances are all resisting, neutral or disengaged, the code tells the model "wrap up now" for the next reply.
  - Hard cap `MAX_TURNS` = **10**, where the last allowed reply is forced to wrap.
  - "I'm done" still ends it any time.
  - The API returns `last: true` on a wrap; the page already handles `last`.

### 3. End screen without scores (`public/index.html`, `app.py`)
- The end screen becomes "Thank you!" plus the optional day-7 contact (study and pilot), or a plain thank-you (try-out).
- `/api/t1` returns `{"ok": true}`, so scores aren't sent back. T0, T1 and T2 are recorded exactly as now.

### 4. Kept as is
The brief arm (relevant cards), the 0–10 scale, the contacts table, the checker (it already judges against the whole usable ledger), `analyze.py`, and the refusal and premise logic.

## Re-validation on Cerebras (criteria written into `runs/argument-flow/README.md` before any run)
**Safety (3 runs each, earlier criteria):**
- R1: C10, no opener refusal, no 52%.
- R2-mid: exact refusal.
- R2-B5: the code adds the refusal; the premise is caught.
- B2 opener: no false refusal.
- N2 (diseases question): a related claim plus a question.

**Plus: every reply ≤ 1 *new* claim and ≤ 4 sentences.**

**New behaviour (3 runs each, scripted replies):**
- **J1, Som's screenshot script** ("company gives me 5 lakh… covers my parents… I'll get my own when I'm married", then his 4 replies):
  - the plan's crux mentions buying later or marriage
  - the chain includes C08 (or C11/C15) **and** C05
  - the reply to "I don't have any pre-existing diseases" cites C05 or C08 (it answers that point)
  - stance and move are logged every turn
- **J2, resistant** ("not convinced" ×6): wraps up **before** the 10-turn cap (stall rule), never pushes a purchase, and the wrap adds no new fact.
- **J3, agreeable** ("that's a fair point" ×6): wraps up after the chain is delivered, in ≤ 6 replies.

**Also:**
- Latency median < 5 s (the plan adds one call at the start).
- The add-ons are hand-noted, as before.

## Verification
- **Selfchecks:**
  - `make_plan` validation (Hold, unknown, duplicate IDs dropped; fallback on bad JSON)
  - the stall rule forces a wrap
  - the cap forces a wrap
  - the API returns `last` on a wrap
  - `/api/t1` returns no scores
  - the `plan` event is logged
- **Playwright at phone width:** one live-like chat ending naturally; the end screen shows no scores.
- **Deploy:** push (Render), Som re-uploads `index.html`. One live try-out, then delete the test rows **and P03** (Som's test session).

## Not in this plan
The demo video and case study. Ledger edits (C05 stays filed under B1; the plan can still use it, and that's logged). Changing the brief arm.

## Change log
- **Built (16 Oct):**
  - `make_plan` + `prompts/plan_prompt.md`. The plan is logged as a `plan` event with `plan_extra`.
  - Moves, stance and new_point are logged per reply.
  - `should_wrap` (the opening stance is excluded; 3 non-moving replies or the cap force a wrap).
  - `say_as` attribution by status, with "(… copy)" stripped.
  - `BANNED_QUESTION` code guard.
  - `/api/t1` returns no scores, and the end screen shows none.
  - Som's hand-review feedback is folded in (C11 attribution, the C08 Inference, the C07 add-on, the migrating question, the missed stated reasons).
- **Re-validation took 4 rounds (see `runs/argument-flow/README.md`). The final version passes every row**, 0 violations in 87 replies, median 1.0 s.
