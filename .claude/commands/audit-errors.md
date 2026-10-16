## Goal
Audit $ARGUMENTS for missing AppError handling. For every function that
raises a raw exception (KeyError, ValueError, TypeError, Exception) or lets
one escape through unchecked dict indexing such as `TASKS[task_id]`,
replace it with the appropriate AppError subclass from utils/errors.py.

## Context
- Canonical error-handling pattern: services/users.py (`get_user` checks
  `if user_id not in USERS:` and raises `NotFoundError("User")`).
- AppError hierarchy: utils/errors.py (AppError, NotFoundError,
  ValidationError).
- Service files hold business logic only: no Flask imports, no `jsonify`.
  `handle_app_error` in routes/api.py turns any AppError into a JSON response.

## Constraints
- Idempotency: if a function already uses AppError correctly (no raw
  `raise`, no unchecked indexing, its existing checks already raise
  NotFoundError/ValidationError), skip it — do not rewrite it. Do not add
  new `isinstance` checks, defaults or edge-case handling the function does
  not already attempt; list such ideas under "Not changed" instead.
  If every function is compliant, reply "No changes needed" and edit nothing.
- Scope lock: edit only $ARGUMENTS and its paired test file
  (services/X.py -> tests/test_X.py). In the test file only ADD tests that
  assert the specific error class; never change existing assertions.
- Do not touch utils/errors.py, routes/api.py or tests/conftest.py.
- Do not add new AppError subclasses — use only existing ones.
- Preserve all existing function signatures.

## Verification
Run `/usr/bin/python3 -m pytest -q` after every function you change — not
once at the end. All tests must pass before you move to the next function.
Finish with a table: function | changed? | why, and the final pytest output.
