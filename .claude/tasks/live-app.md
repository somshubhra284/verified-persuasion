# Plan: a live web version of the study (one link for graders and participants)

Saved to `.claude/tasks/live-app.md` once approved.

## Context
The study only runs as a terminal program (`converse.py`) on Som's laptop, so friends can't use it remotely. The capstone form needs a **Live Project Link**, a **GitHub repo**, a **demo video** and a **case study**.

This plan covers the first two:
- a hosted web app that graders and real participants open from **the same link**
- the public GitHub repo

The demo video (screen-record the live app) and the case study (from `docs/learning-log.md` plus results) come after the participants, as separate tasks.

Decisions already made:
- one link for everyone
- a public repo
- the brief shown inside the site
- OpenRouter → DeepInfra (effort medium) for every session
- the pilot kept separate from the results

## Approach (MVP)
**Hosting: Vercel Hobby (FastAPI, free, no card) + Supabase Free (Postgres) for storage.**
- Vercel serves the page and the API from one link. Function calls can run up to 300 s, which LLM calls with rate-limit waits need.
- Vercel has no disk, so session events go to Supabase over its REST API (plain `httpx`, no SDK).
- Supabase pauses after 1 week without activity, which is fine for a 2-week study.
- Render free was rejected: a ~1 minute cold start would greet graders. HF Spaces and Koyeb now need a paid plan or a card.

**How one link stays clean for the results:**
- The landing page explains the project in 3 lines, then asks: **"I'm taking part in Som's study" / "I'm just trying it out"**.
  - Try-outs get `demo-N` and are never counted. They're capped at 40 a day to protect the OpenRouter credit.
  - Participants who pass screening get the next `P` number. The arm alternates (odd → system, even → brief), as the CLAUDE.md rule says.
  - Declined or screened-out people get `S` numbers, so `analyze.py` can still report them.
- For the pilot only, Som sends `…/?pilot=1`, which gives `pilot-N`, alternating arms.
- At the end, participants see their code (e.g. "P03") to send Som. Day 7: Som sends a T2 link `…/?t2=P03&k=<token>`. The token is an HMAC of the pid, so it needs no extra storage, and `export_sessions.py --t2-link P03` prints it.

## Tasks
1. **Small refactor of `converse.py`** (the CLI keeps working exactly as now): pull out
   - `screen(age, own_policy, govt, t0)`
   - `system_prompt(bucket, reason)`
   - `next_reply(client, model, system, history, ids, log, bucket, turn)`, which is today's retry, `check_reply` and log loop at converse.py:133-149
   - `logger()` taking a pluggable sink
   - The CLI calls these; selfchecks unchanged and must pass.
2. **`app.py` (FastAPI)**, a small JSON API. Session state is rebuilt from the session's own event log, so nothing is held in memory between requests (serverless-safe):
   - `POST /api/start`: mode, consent, age, own policy, government scheme, T0. Screens, assigns pid and arm, returns `{pid, token}`.
   - `POST /api/reason`: classifies (with the one B0 follow-up). System arm: first reply. Brief arm: the brief text.
   - `POST /api/message` (`text` or `done`), `POST /api/brief_done` (seconds), `POST /api/t1`, `POST /api/t2`.
   - The event shape is identical to the CLI's (`ts, pid, event, text, …`), so `check_claims.py`, `--review` and `analyze.py` work unchanged.
3. **Storage sink:** Supabase table `events(id, pid, ts, event, data jsonb)` in production, `sessions/<pid>.jsonl` locally. One small function each.
4. **Frontend `public/index.html`** (vanilla JS + CSS, no build step, phone-friendly):
   - landing → consent → screening form → reason → chat or brief (rendered with pinned `marked`) → after-score → "your code is P03"
   - a "thinking…" state during LLM calls
   - a clear "busy, try again" message if the provider stays rate-limited
5. **`export_sessions.py`:** pulls events from Supabase into `sessions/*.jsonl` so the existing offline pipeline runs as is. `--t2-link <pid>` prints the day-7 link.
6. **Deploy:**
   - **Supabase:** create the project and the `events` table through the connected Supabase tools, with Som's approval.
   - **GitHub:** a public repo through `gh` (logged in as somshubhra284), after a secret scan. `.env`, `sessions/` and `sources/` stay ignored.
   - **Vercel:** Som connects the repo and adds 4 env vars: `OPENROUTER_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `T2_SECRET`.
   - `requirements.txt` with pinned versions; `vercel.json` with `maxDuration: 300` and the data/prompts files included.
   - In the web app, rate-limit retry waits are shortened so a request stays under the 300 s limit.
7. **Docs:**
   - `docs/recruiting.md`: the invite now uses the live link, and the T2 and pilot steps change.
   - CLAUDE.md: files, commands, status.
   - Task log.

**Som's part:**
- Sign in to Vercel with GitHub, click "Import" on the repo, and paste the env vars.
- Approve the Supabase project creation.

## Verification
- Offline: the three selfchecks, plus `app.py --selfcheck`, which uses FastAPI's TestClient with a fake LLM and the file sink. It walks the full system-arm and brief-arm flows, a screen-out, demo vs participant numbering, and a T2 with a good and a bad token.
- Local live: `uvicorn app:app` with the file sink and real DeepInfra. Do one system session and one brief session in the browser, then run `check_claims.py`, `--review` and `analyze.py` on the files.
- Deployed: open the Vercel link on a phone. Do one demo session and one `?pilot=1` session, run `export_sessions.py`, and confirm the logs match the CLI format and record `openrouter:DeepInfra:effort-medium`.

## Not in this plan
The demo video and case study (later, after the participants). Accounts, logins or an admin dashboard (`export_sessions.py` is the admin tool). Changes to the conversation logic, prompts or ledger.

## Change log
(appended as tasks complete)
- **Tasks 1–5 built (16 Oct):**
  - `converse.py` refactored: `screen()`, `system_prompt()`, `next_reply()`, and `logger(pid, sink)` with `file_sink`. The CLI's event order is unchanged; checked offline with a fake model: t0, reason, classify, assistant, user, assistant, t1.
  - `app.py` (FastAPI): `FileStore` locally (`SESSIONS_DIR`) or `SupabaseStore` through stdlib `urllib`. State is rebuilt from each session's events. Retries after "busy" are idempotent. IDs are P/S/demo/pilot. HMAC tokens double as the T2 link key. `RATE_LIMIT_WAITS` is shortened to 5,10,20,30. `app.py --selfcheck` covers every flow.
  - `public/index.html`: vanilla JS, phone-friendly, dark mode. Model text is inserted as plain text only; the brief is rendered with marked@12.0.2.
  - `export_sessions.py`: Supabase → `sessions/*.jsonl`, plus `--t2-link`.
  - `analyze.py` counts `[PS]\d+` (S = website screen-outs) and ignores demo- and pilot-.
  - `classify_eval.pin()` reads `RATE_LIMIT_WAITS`. `httpx` was installed locally for TestClient only.
- **Local live test (DeepInfra, browser at phone width):** the full try-out flow works. Two findings:
  1. **Fix 1 false positive.** Reason "my company gives me 5 lakh group cover…": the model reported the person's *own situation* as `premise`, with `premise_claim` null and `refuse` false. The **code** prepended the refusal. That's the first time fix 1 visibly acted, and it was wrong; it would hit most B2 participants. A conversation-logic change goes to Som.
  2. **Latency:** classify took 9 s and the first reply 55 s. No rate-limit waits were printed, though the SDK's own silent 429 retries are possible.

## Hosting revised by Som (16 Oct): frontend on Hugging Face Spaces (static), backend on Render, database Supabase
Replaces Vercel. What changes:
- **Frontend:** `public/index.html` deploys as a **static** HF Space (free; static Spaces need no paid plan). It calls the API at an absolute `API_BASE` (the Render URL), set in one place in the page.
- **Backend:** `app.py` on a Render free web service from the GitHub repo.
  - Build: `pip install -r requirements.txt`. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
  - `requirements.txt` gains uvicorn. `vercel.json` is removed.
  - Render has no short request timeout, so the default rate-limit waits are fine.
- **CORS:** FastAPI allows only the Space's origin (`ALLOWED_ORIGIN` env).
- **Cold start (free Render sleeps after 15 min, ~1 min wake):** the page calls `GET /api/health` on load, so the backend wakes while the person reads the consent text. If the first real call is slow, the page says "starting up".
- **Day-7 links** point to the Space URL (`APP_URL`).
- Supabase (free) is unchanged: the `events` table, written with the server-side secret key, with RLS on and no policies.

Steps, one at a time with Som:
1. Decisions (Supabase project, regions, names).
2. Supabase table.
3. Code changes (CORS, health, `API_BASE`) plus selfchecks.
4. GitHub repo (public, after a secret scan).
5. Render service plus env vars.
6. HF Space plus upload.
7. End-to-end test on the live links.
- **Step 1 decisions (Som):** a new Supabase project `verified-persuasion` in ap-south-1. Render in Singapore. Names `verified-persuasion` everywhere. Som already has HF and Render accounts.
- **Step 2 done:**
  - Supabase project `verified-persuasion` (ref `ykireedojkbfucxkjcxp`, ap-south-1, created at $0).
  - Table `public.events` (id identity, pid, ts text, event, data jsonb, created_at), indexed on pid and (event, pid). RLS is on with no policies.
  - The docs confirm the `apikey` + `Authorization: Bearer` headers that `SupabaseStore` sends.
- **Step 3 done:**
  - CORS limited to `ALLOWED_ORIGIN` (tested: the allowed origin is echoed back, others get nothing).
  - `GET /api/health`.
  - The page uses `RENDER_API` (https://verified-persuasion-f0vv.onrender.com) when served from hf.space or huggingface.co, else same-origin. It pings health on load and says "Starting up the server…" until the first response.
  - `requirements.txt` gains uvicorn. `SESSION_SECRET` is required when `RENDER` is set.
- **Premise-rule fix verified:** B2 9/9 no false refusal. R2-B5 3/3 refused by code (fix 1 observed working). Learning log entry 12. Latency: first reply 5–60 s (median ~47 s), classify 8–20 s.
- **Step 5a done:** the Supabase secret key is in .env, and a local write+read round trip passed. `SupabaseStore` uses the certifi CA bundle, because python.org macOS builds lack root certificates. The test row was deleted.
- **Step 5b, first Render deploy failed:** `certifi` came only from dev-only httpx, so the clean install crashed at import. It's now pinned in requirements.txt. Render startup was reproduced in a clean venv: /api/health 200.
- **Step 5b done:**
  - Render web service **https://verified-persuasion-f0vv.onrender.com** (Singapore, free) is live. `/api/health` returns 200 and `/` serves the page.
  - A bad token gets 403, so `SESSION_SECRET` is set.
  - A live `/api/start` (a declined try-out) wrote 2 rows to Supabase (ts in UTC); the test rows were deleted.
  - The frontend's `RENDER_API` was updated to the -f0vv URL.
- **Step 6 started:** the Space is huggingface.co/spaces/somshubhra/verified-persuasion. The direct link (the live link) is https://somshubhra-verified-persuasion.static.hf.space. ALLOWED_ORIGIN and APP_URL were added to the local .env; the README carries the live link.
- **Steps 6–7 done:**
  - `ALLOWED_ORIGIN` set on Render. The CORS preflight from the Space origin is allowed.
  - The Space serves `index.html` (the `/` → `/index.html` redirect keeps query params) with `RENDER_API` = -f0vv.
  - **Live end-to-end try-out** (browser → Space → Render → DeepInfra → Supabase): B1 reason, reply with C01+C02 in about 6 s, follow-up with C04+C05, then done and T1. 8 rows in the same shape as the CLI, provider `openrouter:DeepInfra:effort-medium`.
  - `export_sessions.py` pulled it into `sessions/demo-1.jsonl`. `--t2-link` works. `analyze.py` ignores demo-.
  - `docs/recruiting.md` and CLAUDE.md now describe the live-site workflow.
- **Remaining for submission:** demo video, case study (after participants).
