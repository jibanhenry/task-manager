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

## Session 2 — 2026-10-03

### Prompt used
```
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run pytest -v when done.
```
Correction sent in the same session:
```
This was a style refactor, so behavior must not change. Remove the empty-title ValidationError and its test, and keep the docstring, type hints and test_create_task_valid. Run pytest -v when done.
```

### What Claude did
Correct:
- Added a Google-style docstring to `create_task` with `Args` and `Returns`, formatted like `get_user`.
- Used a project error class (`ValidationError`), not a raw exception.
- Added tests and said why: "the project rules require a test whenever a function's errors change", which quotes the rule added after Session 1. The new test asserted `pytest.raises(ValidationError)`, not `Exception`.
- Did not read `USERS` from `services/tasks.py` to check `user_id`. It stopped and asked instead, because that would mean calling `get_user` across services.
- No existing assertions changed, no file reformatted, flake8 warning count unchanged.

Wrong:
- Changed behavior during a style refactor. `get_user` has no input validation, so Claude borrowed the empty-string check from `create_user` and added `if not title or not title.strip(): raise ValidationError("title", "cannot be empty")`. An empty title used to create a task; now it returned a 422. Claude disclosed this itself ("One behaviour change"), but still made the change.
- Its first shell command used `python`, which is not on PATH on my Mac; it retried with `python3`.

After the correction, Claude removed the check, the `Raises:` section, the `ValidationError` import and the empty-title test, and kept the docstring and `test_create_task_valid`. `pytest -v`: 6 passed.

Corrections needed: 1.

### Observation
- The Session 1 test rule worked: Claude cited it directly when adding tests.
- The Architecture rule (only the owning service file touches `TASKS`/`USERS`) also held: Claude asked instead of reaching into `USERS`.
- **Honest failure:** CLAUDE.md did not prevent the behavior change. No rule said a refactor must keep behavior, and the Conventions section pushes the other way: "Follow `services/users.py` as the pattern" plus "raise `ValidationError(field, reason)` for bad input" made adding validation look like following the rules. The word "exactly" in my prompt pointed Claude at `services/users.py` as a whole, so it copied a pattern from `create_user` that `get_user` does not have.
- The `python` vs `python3` retry was minor, but CLAUDE.md said nothing about the environment.

### CLAUDE.md update
Added to Conventions:
```
- Refactor / "match the style of" requests change only docstrings, type
  hints and layout. Do not add validation or change what a function raises
  or returns; list any behavior change you think is needed and ask first.
```
I added this because in Session 2 Claude added an empty-title `ValidationError` to `create_task` during a style refactor, and nothing in CLAUDE.md told it a refactor must keep behavior.

Added to Commands:
```
- Python is 3.9 and the command is `python3`; there is no `python` on PATH.
```
I added this because in Session 2 Claude's first command used `python`, failed, and had to retry with `python3`.
