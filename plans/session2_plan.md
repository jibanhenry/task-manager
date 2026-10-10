# Priority via the API: POST /tasks + new PATCH /tasks/<id>

## Context
Session 1 added `priority` (int 1–5, default 3) to the service layer: the seed records, `create_task(..., priority=3)`, and `_validate_priority()` in `services/tasks.py`. The API doesn't expose it yet. `POST /tasks` ignores `priority` in the body, and there is no PATCH route. This session wires priority into the routes and adds an update path. It follows routes → services: the route only parses the body and calls one service function, and all validation lives in `services/tasks.py`.

"Every task response includes `priority`" is already true for stored records: all seeds have it, and `create_task` stores it. GET, POST and PATCH all return the stored dict, so route-level tests only need to confirm it.

## Order of work
1. Write the new tests first (listed below).
2. Run `/usr/bin/python3 -m pytest -q` and show that the new tests fail and the old ones still pass. Expected failures: `ImportError` for `update_task`. That error stops the whole module from loading, so I'll add the import together with a stub that raises `NotImplementedError` so the failures show up test by test. Route tests will fail with 405 on PATCH and with priority 3 instead of the posted value.
3. Implement the service, then the routes.
4. Verify (see the end of this plan).

## Changes

### `services/tasks.py`: new `update_task`, placed after `create_task`
```python
def update_task(task_id: int, title: str | None = None,
                done: bool | None = None,
                priority: int | None = None) -> dict:
```
- Python 3.9 can't evaluate `str | None` at runtime. Use `Optional[str]` from `typing` instead. The `dict[int, dict]` already in this file works on 3.9.
- `None` means "leave unchanged".
- Order of steps:
  1. `if task_id not in TASKS: raise NotFoundError("Task")`
  2. Validate every supplied field **before mutating anything**, so a bad field never leaves a partial update:
     - `title`: must be a non-empty `str` (after strip). Otherwise `ValidationError("title", "cannot be empty")`. This is the same check as `create_user`'s `name`.
     - `done`: must be a `bool`. Otherwise `ValidationError("done", "must be a boolean")`.
     - `priority`: `_validate_priority(priority)`, which reuses the session 1 helper.
  3. If all three fields are `None`, raise `ValidationError("body", "must include at least one of title, done, priority")`. The message renders as "Invalid body: …" → 422.
  4. Assign each field that isn't `None`, then return `TASKS[task_id]`.
- Google-style docstring with `Args:` (each one says "None leaves it unchanged"), `Returns:`, and `Raises:` (NotFoundError and ValidationError), formatted like `get_user`.
- Leave `create_task`, `get_task`, `process_order` and `get_tasks_for_user` unchanged.

### `routes/api.py`
- Import `update_task`.
- POST: `create_task(data["title"], data["user_id"], data.get("priority", 3))`. This is a pure parse; validation stays in the service. An invalid value such as `"high"` or `0` → `ValidationError` → 422 via `handle_app_error`.
- New route:
  ```python
  @api.route("/tasks/<int:task_id>", methods=["PATCH"])
  def update_task_route(task_id):
      data = request.get_json(silent=True) or {}
      return jsonify(update_task(task_id, data.get("title"),
                                 data.get("done"), data.get("priority")))
  ```
  - `silent=True` returns `None` instead of raising 415/400 for a missing or non-JSON body. With `or {}`, an empty body, a non-JSON body, and `{}` all reach `update_task` with no fields → `ValidationError` → 422.
  - Unknown keys are ignored.
  - If the body is valid JSON but not an object (e.g. `[1]`), `.get` fails → 500. That's an edge case I'm leaving alone; tell me if you want it covered.

### `tests/conftest.py` (new): isolates TASKS between tests
```python
import copy
import pytest
from services.tasks import TASKS

@pytest.fixture(autouse=True)
def restore_tasks():
    saved = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(saved)
```
- **Mutate in place** (`clear` + `update`), not reassign. `routes/api.py`, the service functions and `tests/test_tasks.py` all hold references to the same dict object.
- `deepcopy` is needed because `process_order` and PATCH mutate the inner record dicts.
- The fixture lives in `conftest.py`, so it applies to both test files. No existing assertion changes.

### `tests/test_tasks.py`: service-level only
Only add tests; don't edit existing assertions. The fixture handles isolation, but tests should still update a newly created task where that's natural. Service tests:
- update each of priority, title and done → value stored and returned; other fields unchanged
- `update_task(999, ...)` → `pytest.raises(NotFoundError)`
- priority 0, 6, `"3"`, `True` → `pytest.raises(ValidationError)`
- title `""` and `"   "` → `ValidationError`; done `"yes"` and `1` → `ValidationError`
- invalid field combined with a valid one (e.g. `title="New", priority=0`) → `ValidationError`, and the title is **not** changed (atomicity)
- no fields (`update_task(id)`) → `pytest.raises(ValidationError)`
- isolation check: `process_order(1)` is still run by an existing test; a new test asserts that seed task 1 has `done is False`. It only passes when the fixture restores TASKS, whatever order the tests run in.

### `tests/test_api.py` (new): all route tests
Uses a `client` fixture built from `app.test_client()` (imported from `app.py`). Tests:
- `POST /api/tasks` with `priority: 1` → 201 with `priority == 1`; without priority → `priority == 3`; with `priority: 0` → 422 with an `error` body
- `GET /api/tasks/1` → response includes `priority`
- `PATCH /api/tasks/<new id>` with `{"priority": 2, "done": true, "title": "X"}` → 200 with the updated fields; `PATCH /api/tasks/999` → 404; invalid priority → 422
- PATCH with an empty body, a non-JSON body (`data="not json"`, `content_type="text/plain"`), and `{}` → 422 with an `error` key. Use parametrize.

## Out of scope (not changing; flagging only)
- POST with a missing `title` or `user_id` still gives a `KeyError` → 500, and `create_task` doesn't check that the user exists. Both behaviors predate this change. Tell me if you want them fixed.
- `process_order` has no route and no docstring. Left as is.

## Verification
- `flake8 services/tasks.py routes/api.py tests/`: no new warnings on changed lines. Baseline E302/F401 warnings are allowed.
- Last step: `/usr/bin/python3 -m pytest -q`, with the full output pasted. All tests must pass, old and new. (`python3` on this machine is 3.13 without pytest.)
