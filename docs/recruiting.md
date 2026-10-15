# Recruiting kit

Copy and paste into WhatsApp or DMs. Don't mention the hypothesis, the two versions or "persuasion" before the debrief: knowing them would change how people answer.

Arm assignment is fixed in CLAUDE.md: alternate in recruitment order (P01 system, P02 brief, …). Screened-out and declined people don't take a number.

## 1. Invite
> Hi! I'm doing a small study for my course and need 10 minutes of your time. You'd type with a computer program about one belief on health insurance, and give a 0–100 score before and after. A week later I'll send one short follow-up message (1 minute). Nothing to buy and no one will sell you anything. Your name isn't saved with your answers. Interested?

## 2. Quick self-check (send if they say yes, before fixing a time)
> Just checking you fit the study. Are all of these true?
> - You're 22–45
> - You work, and live in a city
> - You don't have a health insurance policy in your own name (cover through work or family is fine)
> - You're not covered by CGHS, ESIC or PM-JAY (Ayushman Bharat)

If any is false: "Thanks so much! This one needs a narrow group, so I'll skip you this time." The program asks these again and logs any screen-out.

## 3. Consent (the same words the program shows; send beforehand so nothing is a surprise)
> You'll be talking to a computer program, not a person. It wants to understand one belief: "I don't need a health insurance policy of my own." This is not financial advice. Your answers are saved without your name and used only for a study project. You can stop at any time (Ctrl-C).

A stopped session stays in `sessions/` and `analyze.py` counts it as incomplete.

## 4. Running a session
All sessions run on OpenRouter → DeepInfra, reasoning effort medium. That's the code default, so commands need no prefix; every call is checked for host and model. Check your OpenRouter credit before a session day.

**IDs:**
- Pilot = `pilot-1` (system arm) and `pilot-2` (brief arm). The pilot is **not** in the results: `analyze.py` counts only `P01`, `P02`, …
- Participants start at P01 and alternate system/brief (the rule in CLAUDE.md).

**Before each session (1 minute):**
```
.venv/bin/python converse.py --selfcheck && .venv/bin/python check_claims.py --selfcheck
.venv/bin/python -c "from classify_eval import make_client as m; r=m().chat.completions.create(model='openai/gpt-oss-120b', messages=[{'role':'user','content':'ok'}]); print(r.model_extra['provider'], r.model)"
```
The second line must print `DeepInfra openai/gpt-oss-120b`. If DeepInfra is rate-limited, the code waits and retries by itself (up to about 4 minutes).

**The session:**
- System arm: `.venv/bin/python converse.py P0N`. Brief arm: `.venv/bin/python converse.py P0N --brief`.
- They type, you don't help. If they ask you what to answer, say "whatever you actually think".

**Right after a system-arm session:**
1. `.venv/bin/python check_claims.py sessions/P0N.jsonl` (the checker's first pass)
2. `.venv/bin/python check_claims.py --review sessions/P0N.check.jsonl`: label every sentence yourself. Enter keeps the checker's label; n/s/c/u changes it. **Your labels are the metric.**

**After the pilot only:** add both pilots' "why" answers to `data/reasons_heldout.jsonl` as new rows (h-51, h-52, …). Write your bucket label **before** looking at what the classifier said. If the pilot shows something that needs a change, change it before P01, never mid-study.

## 5. Day-7 message (T2)
> Hi! Last step from the study last week, 1 minute. On a scale of 0 (not at all) to 100 (completely), how much do you agree with: "I don't need a health insurance policy of my own"? And did you look into a policy this week (yes/no)?

Then record it: `.venv/bin/python converse.py P0N --t2` and type in their two answers.

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
