# Iteration Log — task-manager CLAUDE.md

## Session 1 — 2026-10-03

### Prompt used
```
Add error handling to the get_task function in @services/tasks.py. Do not change the function signature. Run pytest -v when done.
```

### What Claude did
Correct:
- Raised `NotFoundError("Task")` and imported it from `utils.errors`, instead of letting a raw `KeyError` escape.
- Checked existence with `if task_id not in TASKS:` before indexing, the same way `get_user` does.
- Added a Google-style docstring with `Args`, `Returns` and `Raises`, worded like `get_user` in `services/users.py`.
- Kept the signature unchanged and left `process_order` alone, even though it has the same bug, and said so.
- Ran `flake8`, saw the existing E302 warnings, and did not reformat the file because none were on lines it wrote.
- `pytest -v`: 5 passed (4 before).

Not asked for:
- Added a new test, `test_get_task_not_found_raises_not_found_error`, to `tests/test_tasks.py`. Its reason: the existing `test_get_task_invalid` uses `pytest.raises(Exception)`, which the old `KeyError` also passed, so it could not tell whether the fix worked. It did not change any existing assertion.

Corrections needed: 0.

### Observation
- Conventions (error rule, `services/users.py` pattern, docstring rule) were all followed, almost line for line from `get_user`.
- Commands lint rule ("only fix warnings on lines you changed") was followed: Claude cited CLAUDE.md as the reason for leaving the E302 warnings.
- Do not touch rule on test assertions was followed: it added a test instead of tightening `test_get_task_invalid`.
- Gap: the test rule only covered *new* service functions. `get_task` is an existing function, so adding a test here was Claude's own judgment, not something CLAUDE.md required. A future session could just as easily skip it.

### CLAUDE.md update
Replaced:
```
- New service functions get a test in `tests/test_tasks.py` covering both
  the valid case and the error case.
```
with:
```
- Tests in `tests/test_tasks.py`: when you add a service function OR change
  what an existing one raises, add a test asserting the specific error class,
  e.g. `pytest.raises(NotFoundError)`. `pytest.raises(Exception)` is not
  enough — it also passes on a raw `KeyError`.
```
I changed this because in Session 1 Claude added a `NotFoundError` test for `get_task` on its own, but the old rule only covered new functions, so this behavior was luck rather than something CLAUDE.md guaranteed.
