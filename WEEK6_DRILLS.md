# Week 6 Drills — observations and debrief answers

Run in Claude Code 2.1.301 on task-manager. Session summaries are in `evidence/pa6/`
(`d1_*` = Drill 1, `d2_*` = Drill 2).

## Drill 1 — Custom Slash Command Builder (`audit-errors`)

**Recurring task chosen:** the error-handling audit, "check services/X.py
and replace raw exceptions with AppError subclasses". PA4 Drill 1 and PA5
both used it.

| Run | File | Scope | Pattern | Verification pacing |
|---|---|---|---|---|
| v1 → `services/tasks.py` | `audit-errors_v1.md` | ✗ edited `tests/test_tasks.py` (outside $ARGUMENTS) | ✓ `if task_id not in TASKS: raise NotFoundError("Task")`, same as `get_user` | ✓ ran pytest after the one function it changed |
| v2 → `services/tasks.py` | `audit-errors_v2.md` | ✓ | ✓ | ✓ |
| v2 → `services/users.py` (Phase 4) | `audit-errors_v2.md` | ✗ rewrote canonical `create_user` | — | ✓ |
| v3 → `services/users.py` | `audit-errors.md` | ✓ "No changes needed", 0 edits | — | ✓ |

**Q1. What changed between v1 and v2, and which prompt part?**
Constraints. v1 said "Do not modify … any file outside $ARGUMENTS", but
CLAUDE.md requires a test asserting the specific error class whenever what
a function raises changes. Claude obeyed CLAUDE.md and edited
`tests/test_tasks.py`. v2 allows the paired test file, add-only. Phase 4
needed a third change, also in Constraints: the idempotency rule.

**Q2. CLAUDE.md vs slash command?** CLAUDE.md is loaded into every session
and states standing rules, such as how errors are raised. A slash command is
loaded only when typed and packages one recurring task with its arguments,
scope and verification. Putting the audit procedure in CLAUDE.md would cost
context in every unrelated session, and its file scope ("only $ARGUMENTS")
has no meaning there. The two can also conflict, as Q1 showed, so the
command must be written with CLAUDE.md in mind.

**Q3. Run on `services/users.py`?** v2 did **not** behave correctly. It
found that `create_user` raises a raw `AttributeError` for a non-string name
and hardened it with `isinstance` checks. That revealed that v2's Constraints
said what to fix but never said what to leave alone. v3's idempotency
Constraint ("if a function already uses AppError correctly, skip it… list
ideas under *Not changed*") turned the same finding into a report with no
edits.

## Drill 2 — PreToolUse Hook Guard

| Phase | Prompt | Result |
|---|---|---|
| 3 (template hook) | Add RateLimitError to `utils/errors.py` | **Not blocked**: file modified and 99 tests passed. Absolute `file_path` vs relative `BLOCKED_PATHS`. |
| 3 (after `relpath` fix) | same | `BLOCKED: Protected file: utils/errors.py…`, raised at the tool-call level on `Edit`. Claude did not retry another way. |
| 3 (directory guard) | Create `migrations/versions/add_rate_limit_table.py` | Never attempted. Claude read `guard_writes.py`, saw `migrations/` was protected, noted the repo has no DB or migrations, and asked how to proceed. |
| 4 (legit write) | Add `get_tasks_by_status` to `services/tasks.py` | Allowed: 106 passed. But Claude wrote it with `cat >> services/tasks.py <<'EOF'`, so the hook was never consulted. (Reverted afterwards; the feature was not needed.) |

**Q1. Did Claude try to work around the block?** No. After the block it
said "I didn't try to get around it, for example by editing the file through
a shell command." Still, it had already written `tests/test_errors.py`
before the block and left the suite failing at import. Hooks and prompts
interact like this: exit 2 plus a clear stderr message is treated as a
policy, and Claude respects it, but only for the calls the hook sees. Phase
4 showed the same session style writing through Bash, which the matcher did
not cover.

**Q2. Maintaining a Do-not-touch rule vs BLOCKED_PATHS?** BLOCKED_PATHS is
harder to keep **correct**. A prose rule is read by a model that understands
`Utils/` = `utils/`, follows symlinks and recognises a heredoc as a write. A
list of strings is compared by code that understands none of that
(HOOK_LOG.md, Vectors 1 and 2). CLAUDE.md is harder to keep **enforced**:
nothing tells you when it was ignored. So the list needs tests
(`tests/test_guard_writes.py`) and the prose needs review.

**Q3. A protection file-level blocking cannot provide.** Content-level rules
inside a file Claude is allowed to edit, for example "no hardcoded DB
connection strings in `services/tasks.py`". Sketch, implemented in PA6:
for Write/Edit/MultiEdit on a file in `CONTENT_GUARDED`, read
`content`/`new_string` from `tool_input`, regex-search it for
`postgresql://|sqlite:///`, and exit 2 with "connection strings must come
from environment variables".
