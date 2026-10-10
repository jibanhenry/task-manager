# Task Manager

Flask API for tasks and users. In-memory data, no database.

## Commands
- Python is 3.9 at `/usr/bin/python3`. Plain `python3` on this machine is
  Homebrew 3.13 without the project's packages, and there is no `python`.
- Install: `/usr/bin/python3 -m pip install -r requirements.txt`
- Run tests: `/usr/bin/python3 -m pytest -q` — run before finishing any task;
  all tests must pass. Paste the full output.
- Lint: `/usr/bin/python3 -m flake8 .` — the baseline already has E302/F401
  warnings; only fix warnings on lines you changed, do not reformat whole files

## Architecture
Layered: routes → services → repositories.
- `routes/api.py`: Flask Blueprint `api`. Parses the request, calls one
  service function, returns `jsonify(...)`. No business logic here.
- `services/`: business logic and validation. `services/users.py` is the
  canonical example.
- Repositories: there is no separate repository module yet. The module-level
  dicts `TASKS` (services/tasks.py) and `USERS` (services/users.py) act as
  the data store. Only code in the same service file reads or writes them.
- Cross-service lookups go through the other service's public function:
  `services/tasks.py` may call `get_user(user_id)` to check a user exists,
  but never imports `USERS`.
- `utils/errors.py`: `AppError` base class plus `NotFoundError` (404) and
  `ValidationError` (422). `handle_app_error` in `routes/api.py` turns any
  `AppError` into a JSON error response.
- `app.py`: creates the app and registers the blueprint at `/api`.
- Boundary between `services/` and `routes/`: a route may only read the
  request (`request.get_json(silent=True) or {}`, `request.args`), call one
  service function and `jsonify` the result; every check, default and error
  lives in `services/` — `services/notifications.py` and its routes in
  `routes/api.py` are the canonical example.

## Conventions
- Follow `services/users.py` as the pattern for every service function.
- Type hints on all parameters and return values (e.g. `-> dict`).
- Google-style docstrings with `Args:`, `Returns:`, and `Raises:` sections,
  formatted like `get_user` in `services/users.py`.
- Errors: raise `NotFoundError("Task")` for missing records and
  `ValidationError(field, reason)` for bad input. Never raise raw
  `Exception`, `KeyError`, or `ValueError`, and never return `None` to
  signal "not found".
- Check existence with `if task_id not in TASKS:` before indexing, as
  `get_user` does with `USERS`.
- Write new tests first and show a failing `pytest -q` run before
  implementing; this was lost after `/clear` when it lived only in prompts.
- Tests in `tests/test_tasks.py`: when you add a service function OR change
  what an existing one raises, add a test asserting the specific error class,
  e.g. `pytest.raises(NotFoundError)`. `pytest.raises(Exception)` is not
  enough — it also passes on a raw `KeyError`.
- Refactor / "match the style of" requests change only docstrings, type
  hints and layout. Do not add validation or change what a function raises
  or returns; list any behavior change you think is needed and ask first.

## Do not touch
- `utils/errors.py`: do not change `AppError.__init__`'s signature or its
  `message`/`status_code` attributes — `handle_app_error` reads them.
- Seed records in `TASKS` and `USERS`: tests depend on task ids 1 and 2.
- Existing function signatures in `services/` — `routes/api.py` calls them
  directly. Do not rename or reorder parameters.
- Do not edit existing assertions in `tests/test_tasks.py` to make a change
  pass. Fix the code instead; ask before changing a test.
- `requirements.txt`: do not add dependencies without asking.
- In a tests-only task, do not edit `services/users.py`,
  `services/notifications.py`, `services/tasks.py` or `routes/api.py` to make a
  test pass. Report the production bug and stop (PA5 SA-4 hit exactly this:
  its tests exposed a bug whose fix was in `services/users.py`).
- `tests/conftest.py`: do not rename the autouse fixture `restore_data` or
  drop its `TASKS`/`USERS` restore; every test file relies on it.
- `services/users.py` is the only file that touches `USERS`; notification
  logic belongs in `services/notifications.py`, which uses `get_user()`.
- Do not run git commands (`git worktree`, `git stash`, `git checkout`,
  `git commit`) unless asked; PA5 SA-4b created a worktree on its own.
