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
- Edit only $ARGUMENTS and its paired test file (services/X.py ->
  tests/test_X.py). In the test file, only ADD new tests that assert the
  specific error class (CLAUDE.md test-first rule); never change existing
  assertions.
- Do not modify utils/errors.py, routes/api.py or any other file.
- Do not add new AppError subclasses — use only existing ones.
- Preserve all existing function signatures.

## Verification
Run `/usr/bin/python3 -m pytest -q` after every function you update. All
existing tests must still pass before you move to the next function.
Report the final pytest output when done.
