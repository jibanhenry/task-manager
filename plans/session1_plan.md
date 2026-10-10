# Add `priority` to tasks

## Context
Tasks need a `priority` field: int 1–5 (1 = most urgent), default 3. It goes on the seed records and into `create_task`. Values outside 1–5 are rejected with `ValidationError`. Scope is `services/tasks.py` and `tests/test_tasks.py` only. `routes/api.py` stays unchanged (user's choice); its existing `create_task(title, user_id)` call still works because of the default.

## Order of work
1. **Tests first.** Add the new tests to `tests/test_tasks.py` (listed below).
2. Run `python3 -m pytest -q` and show the output, so you can see the new tests fail. The existing tests should still pass. Expected failures: `KeyError: 'priority'` on records, `TypeError` from the unexpected `priority` keyword, and "DID NOT RAISE" for `ValidationError`.
3. **Implement** the `services/tasks.py` changes below.
4. Run the final verification (see the end of this plan).

## Changes

### `services/tasks.py`
1. Import: `from utils.errors import NotFoundError, ValidationError`.
2. Seed records: add `"priority": 3` to tasks 1, 2 and 3. Keep the ids and all other fields unchanged.
3. New private helper, placed above `create_task`. It is reused by the later PATCH `/tasks/{id}` work, so the check is not inlined:
   ```python
   def _validate_priority(priority: int) -> None:
       """Check that a priority value is allowed.

       Args:
           priority: The priority to check; 1 is most urgent, 5 is least.

       Raises:
           ValidationError: If priority is not an integer from 1 to 5.
       """
       if isinstance(priority, bool) or not isinstance(priority, int) \
               or not 1 <= priority <= 5:
           raise ValidationError("priority", "must be an integer from 1 to 5")
   ```
   The `bool` check is there because `True` and `False` are ints in Python.
4. `create_task(title: str, user_id: int, priority: int = 3) -> dict`
   - Add the new parameter **last**, with a default. Existing parameters are not renamed or reordered, as CLAUDE.md requires.
   - Call `_validate_priority(priority)` first, before allocating an id.
   - Store `"priority": priority` in the new record.
   - Docstring: add `priority:` to `Args:`, noting 1 = most urgent and the default of 3. Add a `Raises:` section: `ValidationError: If priority is not an integer from 1 to 5.`
5. Leave `process_order`, `get_task` and `get_tasks_for_user` unchanged. Don't touch the existing E302 spacing except on lines I edit.

### `tests/test_tasks.py`
Only add tests. Don't edit any existing assertion. Extend the import to `from utils.errors import NotFoundError, ValidationError`, and import `TASKS` to check that nothing was stored. New tests:
- `test_create_task_default_priority`: no priority given → `result["priority"] == 3`.
- `test_create_task_with_priority`: boundaries 1 and 5 are accepted and stored.
- `test_create_task_priority_out_of_range_raises_validation_error`: 0, 6 and -1 each give `pytest.raises(ValidationError)`. Use `pytest.mark.parametrize`.
- `test_create_task_priority_non_int_raises_validation_error`: `"3"`, `3.0` and `True` each give `pytest.raises(ValidationError)`.
- `test_create_task_invalid_priority_not_stored`: `len(TASKS)` is unchanged after a rejected create.
- `test_seed_tasks_have_priority`: every seed task has a priority from 1 to 5.

## Verification
- `flake8 services/tasks.py tests/test_tasks.py`: no new warnings on changed lines. Baseline E302/F401 warnings are allowed.
- **Last step:** run `python3 -m pytest -q` (not `-v`) and paste its full output into the reply. All tests must pass, old and new.
