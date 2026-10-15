# Plan: a lighter journey, short fact cards, a 0–10 scale and no code

Saved to `.claude/tasks/journey-ux.md` once approved.

## Context
Som tested the live site as a participant (P02, the brief arm). Problems:
- The brief arm showed the whole 32-fact sheet with [C01] tags and a sources table: information overload and boring.
- The end screen's "copy your code" felt irrelevant.
- He wants a slow, pinpointed journey, no C-numbers or sources clutter, a 0–10 score, and the end screen to show their score change.

Decisions (Som, 16 Oct):
- **Brief arm:** short fact cards, one at a time, showing **only the facts relevant to the person's own reason(s)**, not the whole ledger.
- **Chat arm:** one point at a time, the source named inside the sentence, no chips or links.
- **End screen:** "you started at X/10, now Y/10", no code.
- **Day 7** (the capstone brief requires "a week later"; the policy question was in Som's own spec): an **optional** phone/email at the end, stored separately. The day-7 page asks the 0–10 score plus "Did you look into a policy this week?".
- **Scale 0–10** everywhere.

**Design consequence, to record honestly:**
- Both arms are now tailored to the person's reason. The comparison changes from "relevant dialogue vs a generic sheet" to **"interactive dialogue vs static relevant facts"**.
- That's a cleaner test of *dialogue*, but it no longer tests *relevance* (both arms have it).
- CLAUDE.md, the README and the learning log get updated to say so. No participant data exists yet: the DB was wiped and the pilot hasn't run.

## Changes
### 1. Brief arm → fact cards (`app.py`, `converse.py`, `public/index.html`)
- `brief_cards(primary, secondary)` parses `data/fixed_brief.md`: 32 bullets, each ending in exactly one `[Cxx]`.
  - It keeps the bullets whose tag is in `reason_claims([primary, secondary])`, primary bucket first, then secondary.
  - It strips the tags and caps at **6 cards**.
  - The text keeps the brief's own wording, which already names the source where needed ("according to the regulator's annual report").
- `/api/reason` for the brief arm returns `{"cards": [...]}` instead of the whole brief.
- The page shows one card at a time ("1 of 5", Next), then "I've finished reading" on the last.
- The log: `brief_read` gets `seconds` plus `cards: [Cxx…]` (which facts were shown), replacing `brief_sha`.
- The sources table and tags are not shown. The full brief stays in the repo as the source of the card text.

### 2. Chat = one point at a time (`prompts/conversation_prompt.md`, `converse.py`)
- Prompt rule: each reply is **one short acknowledgement + exactly ONE fact (≤ 2 sentences) + one question**, at most 1 claim per reply. Build on the person's answer, and pick the next most relevant claim.
- `MAX_TURNS` 4 → **6**, so the journey has room. "I'm done" still ends it any time.
- The page drops the source chips. The source stays named in the sentence (the hard rule). The API keeps returning `sources`; the page just doesn't render them, and the logs are unchanged.

### 3. Scale 0–10 (`converse.py`, `app.py`, `public/index.html`, `analyze.py`, docs)
- `screen()`: T0 < **6** screens out (was < 60).
- The API validates 0–10. The CLI `ask_score` for T0, T1 and T2 becomes 0–10 (age keeps its own range).
- The page: an 11-button 0–10 scale (one tap, nothing preselected) labelled "Not at all … Completely". This replaces the 0–100 slider and number box.
- `analyze.py` deltas are now in 0–10 points (no code change; the label says so).
- The `runs/reversal/inputs/*` intake lines change from `80` to `8` (the conversation lines are unchanged), noted in `docs/reversal-runs.md`.
- CLAUDE.md "Scored 0–100" becomes 0–10, with the date and reason.

### 4. End screen + optional contact (`public/index.html`, `app.py`, Supabase, `export_sessions.py`)
- End (study and pilot): "Thank you! You started at **8/10** and ended at **5/10**."
- Below that, optional: "Can Som send you one quick question in 7 days? Phone or email (optional)" with Save and Skip.
- Try-outs: the same before→after, with no contact box.
- `POST /api/contact {pid, token, contact}` writes to a **separate** Supabase table `contacts(pid, contact, created_at)` (RLS on, no policies), never to `events`.
  - Locally: `sessions/contacts.jsonl` (gitignored).
  - The consent text gains: "At the end you can choose to leave a contact for a 7-day follow-up; it's stored apart from your answers."
- `export_sessions.py --contacts` prints `pid → contact → their day-7 link` (the link already exists).
- The day-7 page uses the 0–10 scale plus the yes/no question.

### 5. Re-validation (criteria written into `runs/journey-ux/README.md` before any run)
- **Selfchecks** (new asserts):
  - `brief_cards` returns only bucket facts, without tags, at most 6
  - screening at < 6
  - 0–10 validation
  - `/api/contact` writes to the contacts store only
  - the end payload has t0 and t1
- **Chat, 3 runs each on Cerebras:** R1, R2-mid, R2-B5, B2, N1 (two reasons), N2 (diseases question).
  - The earlier pass criteria stay.
  - Plus: **every reply cites ≤ 1 claim and is ≤ 3 sentences** (counted).
- **Latency** median < 5 s.
- **Playwright at phone width:** both arms end to end; brief cards for a B2 person show only employer-cover facts; the end screen shows before→after; the contact is saved.

## Deploy
Push (Render redeploys), create the `contacts` table through Supabase, then Som re-uploads `public/index.html` to the Space. One live run per arm, then clear the test rows.

## Not in this plan
The demo video and case study. Changes to the ledger. Removing the full brief file (it stays as the card source).

## Change log
