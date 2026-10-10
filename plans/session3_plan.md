# GET /tasks with optional ?priority=<n> filter

## Context
Right now the API can fetch one task (`GET /tasks/<id>`), create one (POST), and update one (PATCH). There is no way to list tasks. This change adds `GET /api/tasks`, which returns every task, plus an optional `?priority=<n>` that returns only tasks with that priority. It follows routes → services: the route parses the query string and calls one service function; filtering and validation live in `services/tasks.py`.

## Order of work
1. Add the new tests first, plus a `list_tasks` stub that raises `NotImplementedError` so the failures show test by test rather than as one ImportError. Run `/usr/bin/python3 -m pytest -q`: the new tests should fail and the old ones should still pass.
2. Implement the service, then the route.
   (Step 1's run also uses `-q`.)
3. Verify (see the end).

## Changes

### `services/tasks.py`: new `list_tasks`, placed after `get_task`
```python
def list_tasks(priority: Optional[int] = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by priority.

    Args:
        priority: Only return tasks with this priority, from 1 (most
            urgent) to 5; None returns every task.

    Returns:
        A list of task records; empty if no task matches.

    Raises:
        ValidationError: If priority is supplied and is not an integer
            from 1 to 5.
    """
    if priority is not None:
        _validate_priority(priority)
    return [task for task in TASKS.values()
            if priority is None or task["priority"] == priority]
```
- Reuses `_validate_priority` (same file). `_validate_priority` is defined after `get_task`, but that only matters at call time, so placement is fine. I'll put `list_tasks` after `_validate_priority` anyway so it reads top-down.
- Returns a new list built from the stored dicts, the same as `get_tasks_for_user`. `Optional` is already imported; `list[dict]` works on 3.9.
- A valid priority with no matching tasks returns `[]`, not an error. "Not found" applies to single records, not to a filter.

### `routes/api.py`
- Import `list_tasks` (add it to the existing `from services.tasks import update_task` line).
- New route, placed before `/tasks/<int:task_id>` GET:
  ```python
  @api.route("/tasks", methods=["GET"])
  def list_tasks_route():
      priority = request.args.get("priority")
      if priority is not None and priority.isdigit():
          priority = int(priority)
      return jsonify(list_tasks(priority))
  ```
  - Query values are always strings, so the route only converts the type: a string of digits becomes an `int`. Anything else (`"abc"`, `""`, `"-1"`, `"2.5"`) is passed through unchanged, and `_validate_priority` rejects it with `ValidationError` → 422 via `handle_app_error`. The range check stays in the service, so `?priority=0` and `?priority=9` also give 422.
  - I'm not using `request.args.get("priority", type=int)`. On bad input it silently returns `None`, so `?priority=abc` would return every task instead of an error.
  - `jsonify` of a list returns a JSON array.
- Flask routes `GET /tasks` and `POST /tasks` to separate view functions by method; POST is unaffected.

### `tests/test_tasks.py`: service tests (add only, no existing assertions changed)
Every test that uses the priority filter has `filter_by_priority` in its name.
- Import `list_tasks`.
- `test_list_tasks_returns_all`: `list_tasks()` returns all seed tasks. Ids `{1, 2, 3}` are a subset of the result, and `len == len(TASKS)`. This one doesn't use the filter.
- `test_list_tasks_filter_by_priority`: create a task with priority 1 → `list_tasks(1)` contains it and every result has `priority == 1`. Seed tasks (priority 3) are not included.
- `test_list_tasks_filter_by_priority_no_match_returns_empty`: `list_tasks(5)` on the seed data → `[]`.
- `test_list_tasks_filter_by_priority_invalid_raises_validation_error`: priority `0`, `6`, `"3"`, `True` → `pytest.raises(ValidationError)` (parametrized).

### `tests/test_api.py`: route tests
- `test_get_tasks_returns_all`: `GET /api/tasks` → 200, a JSON list containing ids 1, 2 and 3. This one doesn't use the filter.
- `test_get_tasks_filter_by_priority`: `?priority=3` → 200, and every item has `priority == 3`. After POSTing a task with priority 1, `?priority=1` returns only that one.
- `test_get_tasks_filter_by_priority_no_match_returns_empty`: `?priority=5` → 200 with `[]`.
- `test_get_tasks_filter_by_priority_invalid_returns_422`: `?priority=` with `abc`, `0`, `9`, `-1`, and an empty value → 422 with an `error` key (parametrized).

The autouse `restore_tasks` fixture in `tests/conftest.py` already isolates TASKS between tests.

## Out of scope (flagging only)
- No pagination or sorting; results come back in dict insertion order (by id).
- `?priority=+3` or `?priority= 3` give 422 rather than being trimmed or normalized. Tell me if you want those accepted.

## Verification
- `flake8 services/tasks.py routes/api.py tests/`: no new warnings on lines I changed (the baseline E302/F401 warnings are allowed).
- Manual check with the test client is covered by `test_api.py`.
- Last step: `/usr/bin/python3 -m pytest -q`, with the full output pasted. All tests, old and new, must pass.
