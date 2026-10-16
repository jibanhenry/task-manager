## Goal
Scaffold a new API endpoint from $ARGUMENTS, given as `<resource> <METHOD>`
(e.g. `tags POST`): the first word is the resource name (plural, lowercase),
the second is the HTTP method (GET, POST or PATCH). When done, these files
exist or are updated:
- Route file: `routes/api.py` — one new handler on the `api` Blueprint at
  `/<resource>` (POST, GET list) or `/<resource>/<int:id>` (GET one, PATCH).
- Service file: `services/<resource>.py` — create it if missing; holds the
  data store dict, validation and the service function.
- Schema file: `schemas/<resource>.py` — create it if missing (plus an empty
  `schemas/__init__.py`); holds only data: `FIELDS` (response keys) and
  `REQUIRED` (request keys that must be present). No functions.
- Tests: new cases in `tests/test_api.py`.

## Context
- Canonical route pattern: the `/tasks` handlers in `routes/api.py`. This
  project has no separate routes/tasks.py — the task routes in routes/api.py
  play that role. Copy `create_task_route` for POST, `get_task_route` for
  GET one, `update_task_route` for PATCH.
- Canonical service pattern: `services/users.py` (`get_user`,
  `create_user`): type hints, Google-style docstrings, `NotFoundError` /
  `ValidationError` from `utils/errors.py`.
- `handle_app_error` in routes/api.py already turns any AppError into a JSON
  error response; the route does not catch exceptions.
- The `client` fixture in tests/conftest.py gives a Flask test client.

## Constraints
- No business logic in the route handler. The handler may only read the
  request (`request.get_json(silent=True) or {}` / `request.args`), call ONE
  service function, and return `jsonify(...)` with a status code. Every
  check, default and error lives in `services/<resource>.py`.
- Do not modify existing routes, existing service functions or their
  signatures, `utils/errors.py`, `tests/conftest.py` or `requirements.txt`.
- Do not add dependencies (no marshmallow/pydantic): the schema file is plain
  Python constants.
- Data stays in an in-memory dict, like `TASKS` and `USERS`.
- The service must import `REQUIRED` from `schemas/<resource>.py` and raise
  `ValidationError(<field>, "is required")` for each missing key; the schema
  is not decorative.
- `restore_data` in tests/conftest.py only restores TASKS and USERS. If your
  new store is not restored, do not edit conftest.py: make each test create
  its own records and list "conftest needs <STORE> restore" in the report.
- If the method is not GET, POST or PATCH, stop and ask.

## Verification
1. Write the API tests first in tests/test_api.py and show them failing with
   `/usr/bin/python3 -m pytest -q`.
2. After implementing, run `/usr/bin/python3 -m pytest -q`; all tests pass.
3. The happy-path test must assert the exact status: POST -> 201,
   GET/PATCH -> 200. Add one error-path test (422 for a missing required
   field on POST/PATCH, 404 for an unknown id on GET/PATCH).
4. Report the new route line, the files created/changed, and the final
   pytest output.
