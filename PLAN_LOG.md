# PLAN_LOG — Task 1: `priority` field (Plan Mode supervision)

Feature: tasks get `priority` (int 1–5, 1 = most urgent, default 3); `POST /tasks` and `PATCH /tasks/{id}` accept it; every task response includes it; `GET /tasks?priority={n}` filters.

| # | Prompt summary (≤15 words) | Amended? | What you changed (and why) | Output matched amended plan? |
|---|---|---|---|---|
| 1 | Add priority (1–5, default 3) to TASKS seeds and create_task, with tests | Yes | Original plan inlined the 1–5 check in `create_task`, ran tests only at the end, and verified with `pytest -v`. I amended it to: (1) extract the check into `_validate_priority()` in `services/tasks.py`, because PATCH /tasks/{id} (session 2) needs the same check and an inline copy would have to be refactored later; (2) write the new tests first and show a failing `pytest -q` run before implementing; (3) end with `pytest -q` (the PA5 command) and paste the output. | **No (partly).** Steps 1–3 were followed: tests first (11 new cases failed with `KeyError: 'priority'` / `TypeError`, 8 old passed), helper extracted, final `pytest -q` → 19 passed. Two actions were not in the amended plan: (a) it ran `/usr/bin/python3 -m pytest -q` instead of the planned `python3 -m pytest -q`, because `python3` on my Mac is Homebrew 3.13 without pytest, which contradicts CLAUDE.md's "Python is 3.9 and the command is `python3`"; (b) it "wrote 1 memory" (saved the interpreter note to Claude's memory) without asking. I kept the code; (a) shows the `## Commands` section is stale. |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |

## Final check
- `pytest -q`: 
- New priority-filter tests: 
