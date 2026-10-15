# Recruiting kit

Copy and paste into WhatsApp or DMs. Don't mention the hypothesis, the two versions or "persuasion" before the debrief: knowing them would change how people answer.

Arm assignment is fixed in CLAUDE.md: alternate in recruitment order (P01 system, P02 brief, …). Screened-out and declined people don't take a number.

## 1. Invite
> Hi! I'm doing a small study for my course and need 10 minutes of your time. You'd chat with a computer program about one belief on health insurance, and give a 0–100 score before and after. A week later I'll send one short follow-up link (1 minute). Nothing to buy and no one will sell you anything. Your name isn't saved with your answers. Interested?

When they say yes (and pass the self-check): send **https://somshubhra-verified-persuasion.static.hf.space** and say "choose *I'm taking part in Som's study*". Pilot friends get **https://somshubhra-verified-persuasion.static.hf.space/?pilot=1** instead.

## 2. Quick self-check (send if they say yes, before fixing a time)
> Just checking you fit the study. Are all of these true?
> - You're 22–45
> - You work, and live in a city
> - You don't have a health insurance policy in your own name (cover through work or family is fine)
> - You're not covered by CGHS, ESIC or PM-JAY (Ayushman Bharat)

If any is false: "Thanks so much! This one needs a narrow group, so I'll skip you this time." The program asks these again and logs any screen-out.

## 3. Consent (the same words the website shows; send beforehand so nothing is a surprise)
> You're talking to a computer program, not a person. It wants to understand one belief: "I don't need a health insurance policy of my own." This is not financial advice. Your answers are saved without your name and used only for a study project. You can stop at any time by closing this page.

A session that's stopped partway is saved and counted as incomplete.

## 4. Running a session (the live website)
- **Links:**
  - Participants: **https://somshubhra-verified-persuasion.static.hf.space**. They choose "I'm taking part in Som's study".
  - Pilot: **https://somshubhra-verified-persuasion.static.hf.space/?pilot=1**.
  - Graders and anyone curious: the same plain link with "I'm just trying it out". This is never counted.
- **IDs are given by the website:**
  - Participants who pass screening get P01, P02, … in order, alternating system and brief arms, so the CLAUDE.md rule is applied automatically.
  - Screened-out or declined people get S01, S02, ….
  - Pilots get pilot-1 (system) and pilot-2 (brief). Try-outs get demo-N.
  - At the end, participants see their code (e.g. **P03**) and are asked to send it to you. Write it in your recruiting log next to their name, so you know whom to message on day 7.
- **Before a session day:**
  - Open the link yourself about a minute early. The free server sleeps after 15 minutes idle and takes about a minute to wake.
  - Check your OpenRouter credit.
- **Replies take about 1–5 seconds**, longer only on the very first request after the server has slept.
- **Stack:**
  - page on Hugging Face Spaces
  - API on Render (https://verified-persuasion-f0vv.onrender.com)
  - data in Supabase (`events` table)
  - model `openai/gpt-oss-120b` via OpenRouter → Cerebras, effort medium

**After sessions (on your laptop):**
1. `.venv/bin/python export_sessions.py` copies all sessions from Supabase into `sessions/`.
2. For each new system-arm session: `.venv/bin/python check_claims.py sessions/P0N.jsonl`, then `.venv/bin/python check_claims.py --review sessions/P0N.check.jsonl`. **Your labels are the metric.**
3. `python3 analyze.py` prints the results table. It counts P- and S-numbers only.

**After the pilot only:** add both pilots' "why" answers to `data/reasons_heldout.jsonl` as new rows (h-51, h-52, …). Write your bucket label **before** looking at what the classifier said. If the pilot shows something that needs a change, change it before P01, never mid-study.

## 5. Day-7 message (T2)
1. Make that participant's personal link: `.venv/bin/python export_sessions.py --t2-link P0N`
2. Send it:
> Hi! Last step from the study last week, 1 minute: <their link>

The link opens a two-question page (the 0–100 score and "Did you look into a policy this week?"), and the answers are saved to their session. Each link only works for that participant's code.

## 6. Debrief (after T2)
> Thank you! What the study tested: whether a program that only states facts it can source, chosen to answer *your* reason, changes this belief as much as a fixed information sheet. Half the people got the program and half got the sheet. Neither is financial advice, and I'm not recommending any insurer. Happy to share the results when they're written up.

## 7. Recruiting log
Keep it at `sessions/recruiting-log.md`, since it holds names (`sessions/` is gitignored). Never put names in the session files.

| pid | name | date | arm | T0 done | T2 due | T2 done |
|---|---|---|---|---|---|---|
| pilot-1 | | | system | | | |
| pilot-2 | | | brief | | | |
| P01 | | | system | | | |
| P02 | | | brief | | | |
