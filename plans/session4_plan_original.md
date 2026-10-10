# POST /tasks: 422 for missing title/user_id, 404 for unknown user

## Context
`create_task_route` (routes/api.py:26) indexes `data["title"]` / `data["user_id"]`,
so a missing key raises `KeyError` → 500. A missing/non-JSON body makes
`request.get_json()` return None / raise → also not a clean 4xx. `create_task`
(services/tasks.py) never validates title or checks the user exists, so tasks can
be created for nonexistent users. Goal: missing/empty title or missing user_id →
422 (`ValidationError`), unknown user_id → 404 (`NotFoundError("User")`).

## Changes

### 1. `routes/api.py` — parsing only, no logic
```python
data = request.get_json(silent=True) or {}
return jsonify(create_task(data.get("title"), data.get("user_id"),
                           data.get("priority", 3))), 201
```
Same pattern as `update_task_route`. Empty/non-JSON body now reaches the service
and gets a 422 for title.

### 2. `services/tasks.py` — `create_task` validation (signature unchanged)
Validate in this order, all before any write (so 422 wins over 404 and nothing is
stored on failure):
1. `if not isinstance(title, str) or not title.strip(): raise ValidationError("title", "cannot be empty")` — same check/message as `update_task`.
2. `if isinstance(user_id, bool) or not isinstance(user_id, int): raise ValidationError("user_id", "must be an integer")` — covers missing (None). Bool excluded because `True in USERS` would silently match user 1 (same reasoning as `_validate_priority`).
3. `_validate_priority(priority)` (existing).
4. `get_user(user_id)` — cross-service call from `services/users.py`, raises `NotFoundError("User")`; never import `USERS`.

Update the `Raises:` docstring section:
- `ValidationError: If title is missing or empty, user_id is missing or not an integer, or priority is not an integer from 1 to 5.`
- `NotFoundError: If no user exists with the given user_id.`

Type hints left as-is (`title: str, user_id: int`), consistent with how
`priority: int` is already validated at runtime.

### 3. Tests (new tests only; no existing assertion edited)
`tests/test_tasks.py`, asserting specific classes:
- `@parametrize title in [None, "", "   ", 123]` → `pytest.raises(ValidationError)`
- `@parametrize user_id in [None, "1", True]` → `pytest.raises(ValidationError)`
- `create_task("Plan trip", 999)` → `pytest.raises(NotFoundError)`
- invalid input does not grow `TASKS` (missing title, unknown user)

`tests/test_api.py`:
- POST `{"user_id": 1}`, `{"title": "", "user_id": 1}`, `{"title": "X"}`, no body,
  non-JSON body → 422 with `"error"` in body
- POST `{"title": "X", "user_id": 999}` → 404 with `"error"`

Existing tests all use `user_id=1` (exists), so they keep passing.

## Note on scope
The `user_id` integer-type check (rejecting `"1"`/`True` with 422) is slightly
beyond "missing user_id"; without it `"1"` would get a 404 and `True` would
silently attach to user 1. Drop it if you want strictly missing-only.

## Verification
- `/usr/bin/python3 -m pytest -q` (python3 on PATH is 3.13 without pytest) — paste full output
- `flake8 routes/api.py services/tasks.py tests/` — fix only warnings on changed lines
