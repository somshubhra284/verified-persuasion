# Plan: a faster, more responsive chatbot with a better-looking site

Saved to `.claude/tasks/chat-quality.md` once approved.

## Context
Som tried the live site as a participant and found three problems.

1. **Slow.** Render logs show classify 13 s, then replies of 6, 29 and 21 s.
   - A benchmark today on one realistic request: DeepInfra (medium effort) took 33–67 s; **Cerebras (medium) took 0.8–0.9 s**, and still caught the false premise.
   - Lowering the effort on DeepInfra brought it to 3–17 s, but it **missed the false premise**, so that's ruled out.
2. **The person's context isn't used.**
   - "covered by my employer… waste of money, no returns" was classified B2 + secondary **B5**, but the conversation only gets B2's claims. The "no returns" half was never answered.
   - Asked "what diseases have a waiting period?", it sent a **bare** "I don't have a source for that…" and nothing else. The prompt tells it to write only a question after refusing, and the model wrote an empty reply.
3. **The site looks plain;** people should *want* to talk to it.

Outcome: replies in about 1–3 s, conversations that use everything the person said and never dead-end, and a chat interface that looks trustworthy. All before the pilot.

## Changes

### A. Speed: pin Cerebras (`classify_eval.py`)
- Default `OPENROUTER_HOST` = `Cerebras`. Model and effort unchanged (`openai/gpt-oss-120b`, medium). The pin and the host/model check per response stay as they are.
- Update the provider tag, memory, CLAUDE.md and the learning log. This is a setup change, so the re-validation below runs on Cerebras.

### B. Conversation uses the whole reason (`converse.py`, `prompts/conversation_prompt.md`, `app.py`, `check_claims.py`)
1. **Secondary reason counts** *(Som approved)*.
   - Allowed claims = the primary bucket's ∪ the secondary bucket's (still never Hold).
   - The prompt says "main reason (B2 …), also mentioned (B5 …)", and the first reply should address both over the first two turns.
   - `system_prompt(bucket, reason, secondary=None)` and `next_reply` take both. Assistant events log `buckets: [primary, secondary]`.
   - `check_claims.judge` and `check_numbers` use the same union, so the checker judges against exactly what the system was allowed. The CLI passes the secondary too.
2. **Direct questions get the closest sourced answer** *(Som approved; widens the CLAUDE.md "bucket only" rule, to be recorded there)*.
   - Implementation: the prompt lists the bucket claims as "for their reasons" and all other non-Hold claims as "only when they ask directly". The code accepts any non-Hold ID, but the assistant event records which cited IDs were outside the buckets (`question_claims`). The checker's allowed set becomes the whole non-Hold ledger, and its "OTHER claims" list too.
   - When the person asks a factual question, the system may use **any non-Hold ledger claim that answers it**, even from another bucket.
   - If nothing in the whole ledger answers it, it refuses as now.
   - In the example: no claim lists diseases, so it refuses, then offers C11 ("for a pre-existing condition you declare, the waiting period can be at most 3 years, as reported by …") and asks a question back.
   - Logged as `question_claims` so the analysis can count it.
3. **Never a dead end.**
   - The prompt: after a refusal, say what the claims *can* say that's closest, or ask one question about their reason.
   - The code: if the model's reply text is empty, add one neutral question back ("What makes you ask about that?"), so a refusal is never the whole message.
4. **Acknowledge, then evidence.** Prompt rule: start with a short clause reflecting what they said ("Fair point about returns. …"), without agreeing with any factual premise.
5. Add-ons ("which means…", "so you could lose…"): unchanged by decision. They're measured by hand review.

### C. A friendlier interface (`public/index.html`, `app.py`)
- **Landing:**
  - a clear headline and a 3-step "how it works" (tell it your reason → it answers only with checked official data → you score again)
  - a privacy line, and the two buttons
  - a light step indicator (About you → Chat → Wrap-up)
- **Chat** (messaging-app layout):
  - full-height, a sticky composer at the bottom, Enter to send (Shift+Enter for a new line), a textarea that grows
  - a bot avatar and an animated typing indicator
  - **source chips under each bot reply** (e.g. "IRDAI Annual Report 2024–25 ↗") linking to the primary source. `/api/reason` and `/api/message` return `sources` for the cited claim IDs, taken from `data/ledger.json`. Chips show the claims that were actually used, which makes the "only sourced facts" idea visible.
  - refusals styled as a distinct "No source, so not stated" note
- **Scores:** the same 0–100 measure, now a large number field plus a synced slider. The slider has **no default value**, so nobody is nudged toward 50, and Continue stays disabled until a score is set. Labels "Not at all" / "Completely".
- **Brief arm:** a clean reading view with a reading-progress bar and a sticky "I've finished reading".
- **End:** a code card with a Copy button and a clear next step.
- Phone-first, dark mode, system font, no build step, still one file. Model text still goes in as plain text only.

### Re-validation on Cerebras (criteria written into `runs/chat-quality/README.md` before any run)
- **Classifier held-out (50):** ≥ 90% and ≤ 2 wrong (fast now).
- **Earlier checks, 3 runs each:**
  - R1-open: counters with C10, no refusal, no 52%.
  - R2-mid: exact refusal.
  - R2-B5: the code adds the refusal for the premise.
  - B2 openers: no false refusal.
- **New, 3 runs each:**
  1. the screenshot reason ("employer… waste of money, no returns"): at least one B5 claim used within 2 turns
  2. "what diseases have a waiting period?" after a B2 opener: a refusal plus a sourced related claim (e.g. C11) plus a question, never a bare refusal
  3. an off-topic question with no ledger answer ("which insurer is best?"): a refusal plus a question, no insurer named
- Latency is logged from the timestamps. Target: median reply under 5 s.
- The add-ons are hand-labelled as before (not pass/fail).

## Verification
- Selfchecks: `app.py`, `converse.py`, `check_claims.py` and `analyze.py`. New asserts:
  - the allowed set is the union of the two buckets
  - an empty reply after a refusal gets the question added
  - `sources` are returned for the cited IDs
  - the checker uses the same union
- Local: `uvicorn app:app`, then Playwright at phone width through both arms and a try-out. Screenshots reviewed.
- Deploy: push to GitHub (Render redeploys) and re-upload `public/index.html` to the Space. One live try-out on the Space link, confirming the Supabase rows show `openrouter:Cerebras:effort-medium`.

## Not in this plan
The demo video and case study. Changes to the ledger. Tuning away the add-ons (they're measured by decision).

## Change log
- **A + B built (16 Oct):**
  - The Cerebras pin is the default.
  - `converse.py`: `usable_claims()`, `reason_claims([primary, secondary])`, `secondary_of()`, `system_prompt(bucket, reason, secondary)` with `{secondary_line}` and `{other_claims}`, and `next_reply(..., secondary)`. Assistant events log `buckets` and `question_claims`. `check_reply` validates against all usable IDs, rejects an empty reply without a refusal, and turns an empty reply after a refusal into `REFUSAL + FOLLOW_UP`. The CLI passes the secondary bucket.
  - The prompt is rewritten: claims for their reasons, other checked claims for direct questions only, refusals must continue the conversation, acknowledge first, cover both reasons.
  - `check_claims`: the judge's OTHER list and the number pool are now the whole usable ledger, and the `bucket` parameter is dropped. Two number asserts are now label-agnostic (12 and 52 match other claims).
  - `app.py`: the secondary bucket goes through the classify → system prompt → next_reply path, the API returns `sources` for cited IDs, and a selfcheck covers both.
- Re-validation criteria are written in `runs/chat-quality/README.md`.
- **Re-validation on Cerebras:** see `runs/chat-quality/README.md`. Everything passes after the history-encoding fix; median latency 1.0 s. The duplicate-refusal cleanup was added in code.
