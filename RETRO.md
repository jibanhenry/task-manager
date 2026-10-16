# RETRO — PA6: Enforce, Automate, and Reflect

(The PA5 retrospective is kept as `RETRO_PA5.md`.)

## 1. Slash command value — which command saved the most prompt-writing effort?

`/project:scaffold-endpoint` saved the most effort (COMMAND_LOG.md, the
scaffold-endpoint row; iteration rows 5–6). The second invocation was two
words, `tags GET`. Without the command, the ad-hoc prompt would have had to
re-state everything the file now carries:

- the three target files (`routes/api.py`, `services/tags.py`,
  `schemas/tags.py`);
- that the `/tasks` handlers in `routes/api.py` are the pattern (this repo has
  no `routes/tasks.py`);
- the no-business-logic rule for routes;
- "schema is plain constants, no marshmallow";
- tests first with the exact 201/200/422/404 status codes;
- the `/usr/bin/python3` pytest command;
- since v2, the warning that `restore_data` does not reset new stores.

That is roughly 30 lines, retyped every time and slightly different each time.
The command is better for two reasons. First, the lesson from one run is
carried into the next. The v2 Constraint I added after the `tags POST` run
(row 5: `TAGS` not restored between tests) made the `tags GET` run report
"conftest needs TAGS restore" without being asked. An ad-hoc prompt would have
lost that fix after `/clear`, as `-q` and tests-first were lost in PA5.
Second, a fixed text lets me fix one specific failure, such as the
audit-errors idempotency gap (rows 3→4), and check the fix the next time it
runs.

## 2. Hook reliability — what happened during the Part B bypass attempts?

Both vectors bypassed the hook before the fixes (HOOK_LOG.md).

- **Vector 1.** I asked Claude to "Modify Utils/errors.py". It checked
  `ls -di Utils utils`, saw that the two paths are the same file, and ran
  `sed -i … Utils/errors.py`. The protected `utils/errors.py` changed even
  though my Mac reports `Utils/errors.py` and `utils/errors.py` as one inode
  (74).
- **Vector 2.** `cat >> utils/errors.py <<'EOF'` appended a class with the
  hook registered and Bash already in the matcher, because the Bash branch
  only looked for dangerous commands and never for write targets.
- **Same pattern elsewhere.** The Drill 2 template blocked nothing (absolute
  vs relative path), and the Part A `rm -rf` rule missed
  `find … -exec rm -rf {} +`.

So "the rule is in settings.json" only means the script runs. Whether it
enforces anything depends on two things: the matcher seeing the tool Claude
actually picks, and the script's comparison matching how the OS and the
shell interpret the path. Claude chose Bash heredocs on its own in Drill 2
Phase 4 and in both scaffold runs (COMMAND_LOG.md, last note), so a
`Write|Edit|MultiEdit` matcher covered only part of the real writes. A hook
counts as enforced only once a bypass attempt against it has failed, and
the fix itself needs testing: my first Vector 2 fix blocked a read-only
`ls … 2>&1; head utils/errors.py`.

## 3. Advisory vs deterministic — a rule I left in CLAUDE.md on purpose

I left this rule advisory: "In a tests-only task, do not edit
`services/users.py`, `services/notifications.py`, `services/tasks.py` or
`routes/api.py` to make a test pass."

It depends on the task, not the path. `/project:audit-errors` (row 2) and
`/project:scaffold-endpoint` (rows 5–6) must edit exactly those files. A
PreToolUse hook only sees one tool call's JSON and cannot tell whether this
session is a tests-only one. Adding those paths to `BLOCKED_PATHS` would block
legitimate work. The advisory rule has held so far: `/project:fill-tests`
(row 7) found the real `create_user` bug, marked it `xfail(strict=True)` and
left `services/users.py` untouched. The `fill-tests` command also repeats the
rule in its Constraints.

**Graduation condition:** I will move this rule into `guard_writes.py`
as soon as either of these happens:

- (a) Any `fill-tests` row in COMMAND_LOG.md records "Stayed in scope = No"
  because a production file was edited.
- (b) I add a second tests-only command.

The implementation is ready to write. `/project:fill-tests` writes `tests/`
to `.claude/scope.txt` as its first step, the hook blocks writes outside the
paths listed there while the file exists, and the command deletes the file in
its Verification step. This is the scope-file design from RETRO_PA5.md §4.

## 4. Limits of hooks — a rule PreToolUse could not enforce

The rule I wanted enforced is CLAUDE.md's "run `pytest -q` before finishing
any task; all tests must pass." The Drill 2 Phase 3 re-run shows why. Claude
first wrote `tests/test_errors.py` for `RateLimitError`. The hook then blocked
the edit to `utils/errors.py`, and Claude stopped. It left the repo with a
test file that failed at collection (`ImportError: cannot import name
'RateLimitError'`). Its report mentioned this, but nothing forced it to clean
up.

PreToolUse is the wrong event for this. It fires before each single tool call
and sees only that call's input. "The session ends with a green suite" is a
property of the end state, and no single Write, Edit or Bash call carries it.
Running pytest before every call would test the code before the change, not
after.

The right mechanism is a **Stop hook**, which fires when Claude tries to
finish. It would run `/usr/bin/python3 -m pytest -q`; on failure it would exit
2 with the failing test names, so Claude has to continue and either fix the
code or remove the orphaned test. A PostToolUse hook on `services/` edits
would give earlier feedback. CI on push is the backstop for anything a local
hook misses.
