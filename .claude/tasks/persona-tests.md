# Plan: test the live platform with 10 personas, one by one

Saved to `.claude/tasks/persona-tests.md` once approved.

## Context
Som wants the live platform tested end to end with 10 personas (SIM01–SIM10), one at a time, with the results stored. Each persona has a fixed arm (system or brief) and an opening line.

Som's choices:
- **Claude drafts each persona reply in character; Som approves or edits it before it's sent.**
- **T0 = 8** for everyone except Anita (**T0 = 5**, i.e. 55 on the old scale, so she should be screened out before the reason question).
- **Som gives every T1.**

These are simulated users, so they must never be counted as study data.

## Changes
1. **A `sim` mode in `app.py`** (small):
   - `POST /api/start` accepts `mode: "sim"` with `arm: "system" | "brief"` and an optional `label` (the persona name).
   - IDs are `sim-N`, never P/S/pilot, so `analyze.py` already ignores them (it counts `[PS]\d+` only).
   - The `start` event logs the label.
   - The arm is only choosable in sim mode. Sim mode shares the try-out daily cap.
   - Selfcheck: a sim session gets the requested arm, never takes a P-number, and isn't counted by `analyze.py`.
2. **`sim.py`, a small driver for the live API** (Render + Supabase + Cerebras, the real platform). Commands:
   - `start <SIMxx> <arm> <t0> "<opening line>"` (consent yes, age from the persona or 28, no own policy, no government scheme). It prints the bot's first reply, or the screen-out, or the brochure summary (8 cards, 32 facts).
   - `say <SIMxx> "<reply>"`: prints the bot's reply, its move, and whether it wrapped.
   - `done <SIMxx>` and `t1 <SIMxx> <score>`.
   - Session tokens are kept in the scratchpad, never in the repo.

## Running it, one persona at a time
For each persona:
1. Start it, and show Som the bot's first reply (or the brochure, or the screen-out).
2. Draft the persona's reply, keeping to their words and attitude (sceptical, not a pushover).
3. **Som approves or edits it, then I send it.**
4. Repeat until the bot wraps up, or it's naturally over (Som can say "done").
5. Ask Som for T1, then send it.
6. Move to the next persona.

| ID | Persona | Arm | Opening | What I'll check |
|---|---|---|---|---|
| SIM01 | Arjun, 29 | system | employer 5 lakh + parents; buy when married | B2+B4; answers employer cover first; crux "buy later"; C08/C05 reach him |
| SIM02 | Riya, 24 | brief | on dad's family policy | B7; the same 8-card brochure |
| SIM03 | Farhan, 32 | system | "most claims rejected… uncle… pre-existing… scam" | B3; premise "most rejected" countered with C10 (no refusal); the uncle's pre-existing-disease story met with C12/C11/C29 if relevant; no endorsement of "scam" |
| SIM04 | Karthik, 34 | brief | buy around 40 | B4; brochure |
| SIM05 | Pooja, 28 (Hinglish) | system | premium waste, FD, healthy | B5+B1 from Hinglish; FD/savings → cost claims (C02/C18/C21) and health → C05 |
| SIM06 | Neel, 27 | brief | never been to hospital, freelance income | B1+B5; brochure |
| SIM07 | Sunil, 35 | system | "Ayushman Bharat, 5 lakh free for everyone" | B6; the false premise "free for everyone" contradicted by C22/C23 (not refused, since a claim covers it); screening "covered by PM-JAY?" = no |
| SIM08 | Meera, 30 | brief | claims paperwork, TPAs, exclusions | B3; brochure |
| SIM09 | Dev, 26 | system | "never really felt the need" | B0 → one follow-up question → (my drafted answer, Som approves) → classify; ends cleanly if still B0 |
| SIM10 | Anita, 30 | (system) | none | T0 = 5 → `screened_out` **before** the reason question; no LLM call |

## Storing the results
- **After all 10:**
  - `export_sessions.py` pulls the sim sessions.
  - `check_claims.py` runs on the 5 system sims as a first pass. I note any unsupported or misattributed sentences for Som's later hand review (no `--review` for sims unless Som wants it).
- **`runs/personas/SIMxx.md` per persona:**
  - the opening line and classification (primary/secondary)
  - the argument plan (crux and chain)
  - the full transcript with claim IDs, moves, stances, refusals and premises
  - latency, checker flags, T0/T1 (marked **simulated**)
  - my notes: what worked, what didn't, against the checks above
- **`runs/personas/README.md`:** a summary table (ID, arm, bucket, replies, how it ended, T0→T1, issues) and the cross-persona findings. The raw logs go in `runs/personas/logs/`.
- **Then, with Som's OK,** the sim rows are deleted from Supabase so the live DB stays empty for the pilot.

## Verification
- Selfchecks pass, including sim mode.
- After deploying (a push redeploys Render; **`index.html` is unchanged**, so there's no Space upload), one sim start confirms the arm override works live.
- Every persona run is reviewed against its check column. Problems found are reported, **not fixed mid-run**, so the 10 runs test one version. Fixes are planned afterwards if needed.

## Not in this plan
Changing the chatbot or the brochure during the runs. Counting any sim as study data.

## Change log
- **Built:** sim mode in app.py (arm and label chosen, sim-N ids, screening applies, shares the try-out cap; selfcheck) and `sim.py` (a live-API driver: start/say/done/t1/show; tokens kept in the scratchpad).
- **Ran (16 Oct):** all 10 personas on the live stack (sim-2 … sim-11; sim-1 was a declined probe). Every persona reply approved by Som; every T1 from Som. Simulated ΔT1: chatbot −0.4 (n=5), brochure −0.75 (n=4); SIM10 screened out at T0 5 before any LLM call.
- **`sim.py`:** reads retry on Supabase HTTP 555 (seen twice mid-run).
- **Stored:** `runs/personas/` — SIM01–SIM10.md (rendered from the logs + `notes.json`), README.md (summary table + 11 cross-persona findings), `logs/` (raw sim-2…sim-11 JSONL, checker `.check.jsonl` and `checker-output.txt`). Checker first pass on the 5 chatbot sims: 1, 0, 2, 2, 1 flags (SIM09's is a user echo).
- **Open:** delete sim rows from Supabase (needs Som's OK); fixes proposed in README findings 1–10, to plan separately.
