# Plan: remove the persona-run files, keep an honest stress-test note

Som (16 Oct): options 1 + 2. Remove the persona sessions from the repo; the write-up mentions them only as pre-pilot stress tests, never as participants.

## Remove (git rm)
- `runs/personas/` (SIM01–SIM10.md, README, notes.json, logs/)
- `runs/persona-fixes/` (replay logs, scores, README)
- `sim.py`
- `.claude/tasks/persona-tests.md`, `.claude/tasks/persona-fixes.md`

## Edit
- `docs/learning-log.md` #17: retitle "Pre-pilot stress tests found what the scripted tests didn't"; say they were scripted test conversations, not participants; drop names, scores and the deleted paths; keep the findings and fixes.
- `converse.py:179`, `:213`: "(SIM07)" → "(stress test)".
- `app.py:154`: keep sim mode (test sessions, never counted); comment → "test sessions".

## Not touched
- Git history (commits `3b30f7e`, `c644219`, `9888069` still contain the files). Rewriting public history = force-push; only if Som asks.
- The other test runs (`runs/reversal`, `argument-flow`, `chat-quality`, …): scripted tests, already labelled; reversal is required by the brief.
- The local `persona-case-study.md` (outside the repo).

## Verify
`converse.py --selfcheck` + app selfcheck; `git grep` for SIM0/persona/sim.py is empty. Commit + push only when Som says.

## Change log (16 Oct)
- `git rm`: runs/personas/, runs/persona-fixes/, sim.py, .claude/tasks/persona-tests.md, .claude/tasks/persona-fixes.md.
- `docs/learning-log.md` #17 retitled "Pre-pilot stress tests…"; states they were tests, not participants; names, scores and deleted paths dropped; findings and fixes kept.
- `converse.py` 179/213 and `app.py` 154 comments reworded.
- Verified: git grep for persona/SIM/sim.py/simulat/names is empty; converse + app selfchecks ok. Not committed yet.
