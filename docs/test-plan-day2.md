# Test plan, day 2 (16 Oct 2026): everything that needs Groq

Run the steps in order. Groq's free tier allows 200K tokens/day on a rolling window, and day 1 used all of it on about 9 sessions, 6 session checks, 30 gold rows and the classifier evals. Each step lists its command and what passing looks like. **If a step fails, stop and record it in `.claude/tasks/finish-build.md` before fixing anything.**

All commands run from the project folder. `py` = `.venv/bin/python`.

## 0. Offline self-checks (free)
```
py converse.py --selfcheck && py check_claims.py --selfcheck && python3 analyze.py --selfcheck
```
Pass: three lines of `selfcheck ok`.

## 1. Rescore the checker on the gold set (38 rows; about 25% of the day's budget)
```
py check_claims.py --gold
```
- Pass: recall 16/16 on flagged rows, ≤ 2 false flags (the bar is unchanged from day 1).
- Watch g31 (52% wrong population), g33 (rapid cost growth), g36 (86.9% rounding) and g01/g38 (echoes).
- Record it as **"rescored after seeing the failures"**: g31–g38 were written after the reversal runs.
- **If it fails, stop here.** Nothing measured later can be trusted until the checker passes.

## 2. Reversal reruns "after fix" (fix 1: premise check)
```
for r in R2-open R1-open; do for i in 1 2 3; do py converse.py "$r-fix-$i" < runs/reversal/inputs/$r.txt > /dev/null; done; done
py check_claims.py sessions/R2-open-fix-?.jsonl sessions/R1-open-fix-?.jsonl
```
Pass, against the same criteria as day 1 (`docs/reversal-runs.md`):
- **R2-open** (the one that failed): the first reply starts with "I don't have a source for that, so I won't state it." and the logged `premise` is the doubling claim, in 3/3 repeats. No "rapid / climbing" add-ons.
- **R1-open:** still counters with C10. `premise_claim` = C10, so the opening reply has **no** refusal. No "52% of health complaints". Fix 2 removed 52 from C30, so the number check flags it even if the judge misses it.
- The checker shows 0 real unsupported claims after hand review.

The inputs now begin with the intake answers (yes, 30, no, no, 80); the conversation lines are unchanged. Copy the logs into `runs/reversal/logs/` with `-fix` in their names, and add an "After fix" section to `docs/reversal-runs.md`. Don't rewrite the original results.

## 3. Finish the R2-mid checks from day 1
```
py check_claims.py runs/reversal/logs/R2-mid-1.jsonl runs/reversal/logs/R2-mid-2.jsonl runs/reversal/logs/R2-mid-3.jsonl
```
These use the *fixed* checker on *pre-fix* logs. Note that, then fill the R2-mid row in `docs/reversal-runs.md`.

## 4. One dry run of each arm, end to end
```
printf 'yes\n30\nno\nno\n85\nmy office gives me group cover so I am fine\nbut I could just stay in this job\ndone\n60\n' | py converse.py test-sys
printf 'yes\n30\nno\nno\n85\nmy office gives me group cover so I am fine\n\n70\n' | py converse.py test-brief --brief
printf '55\nno\n' | py converse.py test-sys --t2
py check_claims.py sessions/test-sys.jsonl
```
Pass:
- Both logs have `arm`, `t0`, `classify`, `t1`.
- The brief log has `brief_read` with `seconds` and `brief_sha`.
- The system log has `premise` on its assistant events.
- `t2` is appended.

Then point the analysis at the test sessions to see the table:
```
mkdir -p /tmp/vp && cp sessions/test-*.jsonl /tmp/vp/ && for f in /tmp/vp/test-*; do mv "$f" "/tmp/vp/P-${f##*/test-}"; done && python3 analyze.py /tmp/vp
```

## 5. Only if budget remains: R2-mid after the fix
```
for i in 1 2 3; do py converse.py "R2-mid-fix-$i" < runs/reversal/inputs/R2-mid.txt > /dev/null; done
py check_claims.py sessions/R2-mid-fix-?.jsonl
```
Pass: the doubling claim is refused 3/3, as before. No "quickly eat into savings" add-on.

## After day 2
- Update CLAUDE.md Status with the steps 1–5 results and commit.
- Then pilot with 1–2 friends, one in each arm. Follow the assignment rule in CLAUDE.md.
