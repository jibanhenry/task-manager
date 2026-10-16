# Use when a service file in services/ has functions or error paths without tests that assert the specific error class; do not use when you also need to change production code — a failing test that exposes a bug is reported, not fixed.

## Goal
Find every public function in $ARGUMENTS that has no test, and every
documented `Raises:` path that no test covers, then add pytest cases so each
one is covered. Tests go in the paired file (services/X.py ->
tests/test_X.py); create that file if it does not exist.

## Context
- Error classes: `NotFoundError` and `ValidationError` in utils/errors.py.
- Existing style: tests/test_tasks.py (plain functions,
  `pytest.raises(NotFoundError)`) and tests/test_notifications.py
  (`@pytest.mark.parametrize`, `client` fixture for HTTP-level checks).
- tests/conftest.py has the autouse fixture `restore_data`, which restores
  `TASKS` and `USERS` after every test, so tests may mutate them freely.
- PA5 SA-4 lesson: a test that only checks a key exists passed while the
  value was wrong — assert values, not just presence.

## Constraints
- Tests-only task: edit only the paired test file. Do not edit $ARGUMENTS,
  any other file in services/, routes/api.py or tests/conftest.py.
- Assert the specific error class (`pytest.raises(ValidationError)`), never
  `pytest.raises(Exception)`.
- Do not change or delete existing tests or assertions.
- If a new test fails because the production code is wrong, do not fix the
  code and do not weaken the test: mark it
  `@pytest.mark.xfail(reason="<bug>", strict=True)` and report the bug.
- Skip functions that are already fully covered; say so in the report.

## Verification
Run `/usr/bin/python3 -m pytest -q` after adding the tests for each function.
Final run must show 0 failed (xfail allowed only for reported bugs). Report a
table: function | tests added | covered paths | bugs found.
