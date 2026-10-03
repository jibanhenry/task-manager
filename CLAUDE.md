# Task Manager

Flask API for tasks and users. In-memory data, no database.

## Commands
- Install: `pip install -r requirements.txt`
- Run tests: `pytest -v` — run before finishing any task; all tests must pass
- Lint: `flake8 .` — the baseline already has E302/F401 warnings; only fix
  warnings on lines you changed, do not reformat whole files

## Architecture
Layered: routes → services → repositories.
- `routes/api.py`: Flask Blueprint `api`. Parses the request, calls one
  service function, returns `jsonify(...)`. No business logic here.
- `services/`: business logic and validation. `services/users.py` is the
  canonical example.
- Repositories: there is no separate repository module yet. The module-level
  dicts `TASKS` (services/tasks.py) and `USERS` (services/users.py) act as
  the data store. Only code in the same service file reads or writes them.
- `utils/errors.py`: `AppError` base class plus `NotFoundError` (404) and
  `ValidationError` (422). `handle_app_error` in `routes/api.py` turns any
  `AppError` into a JSON error response.
- `app.py`: creates the app and registers the blueprint at `/api`.

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
- New service functions get a test in `tests/test_tasks.py` covering both
  the valid case and the error case.

## Do not touch
- `utils/errors.py`: do not change `AppError.__init__`'s signature or its
  `message`/`status_code` attributes — `handle_app_error` reads them.
- Seed records in `TASKS` and `USERS`: tests depend on task ids 1 and 2.
- Existing function signatures in `services/` — `routes/api.py` calls them
  directly. Do not rename or reorder parameters.
- Do not edit existing assertions in `tests/test_tasks.py` to make a change
  pass. Fix the code instead; ask before changing a test.
- `requirements.txt`: do not add dependencies without asking.
