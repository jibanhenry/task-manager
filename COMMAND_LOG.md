# COMMAND_LOG — PA6 Task 1: Slash Command Library

All runs used Claude Code 2.1.301 started in the task-manager root, so
`.claude/commands/`, `.claude/settings.json` and CLAUDE.md were loaded. Each
command was invoked with `/<name>`, which is the same command as
`/project:<name>`. Session summaries and diffs are in `evidence/pa6/`.

## One row per command (final version)

| Command invoked | $ARGUMENTS | Stayed in scope? | What worked / what I changed |
|---|---|---|---|
| `/project:audit-errors` | `services/users.py` (the canonical file; earlier versions were also run on `services/tasks.py`) | Yes | **Changed:** v2 rewrote `create_user` in the canonical `services/users.py`, adding `isinstance` checks and `max(..., default=0)`. So I added the idempotency Constraint ("if a function already uses AppError correctly, skip it — do not add `isinstance` checks… list ideas under *Not changed*"). v3 replied "No changes needed", made 0 edits, and listed the same two edge cases as findings. |
| `/project:scaffold-endpoint` | `tags POST`, then `tags GET` | Yes (both runs) | **Changed:** the `tags POST` run produced a `schemas/tags.py` whose `REQUIRED` nothing read, and a `TAGS` store that `restore_data` does not reset. v2 added two Constraints: the service must use `REQUIRED`, and a non-restored store must be reported instead of editing conftest.py. The `tags GET` run then reported "conftest needs TAGS restore" on its own. |
| `/project:fill-tests` | `services/users.py` | Yes | **Worked first time:** it wrote 22 cases in a new `tests/test_users.py` and touched nothing else. It hit the real `max(USERS.keys())` → raw `ValueError` bug and followed the xfail Constraint (`strict=True` plus a report) instead of editing `services/users.py`, so the result was `124 passed, 1 xfailed`. |

## Iteration history (how each command got to its final form)

| # | Version | Invocation | Scope? | Observation | Change made to the command file |
|---|---|---|---|---|---|
| 1 | audit-errors v1 (`audit-errors_v1.md`) | `services/tasks.py` | **No** | It correctly fixed `process_order` (`TASKS[task_id]` raised a raw `KeyError`; it now raises `NotFoundError("Task")`), going from 1 failed to 97 passed. But it also edited `tests/test_tasks.py`, which v1 forbade ("any file outside $ARGUMENTS"). CLAUDE.md's test-first rule pulled it there: the command and CLAUDE.md contradicted each other. | Constraints: allow the paired test file `tests/test_X.py`, add-only, never change existing assertions; name `routes/api.py` explicitly. |
| 2 | audit-errors v2 (`audit-errors_v2.md`) | `services/tasks.py` | Yes | Same fix. It edited only `services/tasks.py` and its paired test file, and ran pytest after the change (1 failed → 97 passed). | — |
| 3 | audit-errors v2 | `services/users.py` (Drill 1 Phase 4) | **No** | The canonical file was modified: `create_user` got new `isinstance` checks and `max(..., default=0)`. The suite went to 103 passed, but this was not an error-handling fix. | Idempotency Constraint plus a "Not changed" list. Verification now says "after every function you change — not once at the end" and requires a function/changed?/why table. Scope lock now names `utils/errors.py`, `routes/api.py` and `tests/conftest.py`. |
| 4 | audit-errors v3 (final `audit-errors.md`) | `services/users.py` | Yes | "No changes needed"; 0 edits. Its table showed `get_user`, `list_users` and `create_user` as unchanged. | — |
| 5 | scaffold-endpoint v1 | `tags POST` | Yes | It wrote tests first (5 failed), then created `schemas/__init__.py`, `schemas/tags.py`, `services/tags.py` and the `POST /tags` route (route only reads JSON, calls `create_tag`, returns 201), ending at 102 passed. Two gaps: `REQUIRED` unused, and `TAGS` is not reset between tests. | Two Constraints added (see the scaffold-endpoint row in the first table). |
| 6 | scaffold-endpoint v2 (final) | `tags GET` | Yes | It added `list_tags` and the `GET /tags` route, going from 1 failed (405) to 103 passed. It reported "conftest needs TAGS restore" instead of editing the protected conftest. | — |
| 7 | fill-tests v1 (final) | `services/users.py` | Yes | 103 → `124 passed, 1 xfailed`. The xfail documents the empty-`USERS` `ValueError`, the same edge case audit-errors v3 listed under "Not changed". | — |

Observation across all runs: Claude wrote many files through Bash heredocs
(`cat >> tests/test_api.py <<'EOF'`, `cat >> services/tags.py <<'EOF'`)
instead of the Write or Edit tools. This is why the hook's matcher has to
include Bash (HOOK_LOG.md, Vector 2).
