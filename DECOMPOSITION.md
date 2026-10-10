# DECOMPOSITION — Task 2: user notification preferences

Written before opening Claude Code for Task 2.

## Feature
- Users get `notification_pref`: one of `email`, `sms`, `none` (default `none`), stored on the user record in a nullable field.
- `PATCH /users/{id}/notifications` updates it; an invalid value raises `ValidationError` (422).
- `GET /users/{id}/notifications` returns the current preference.
- The user list and user detail endpoints include `notification_pref`.

## How this repo maps onto the layers
- There is no `models/` package. The "User model" is the `USERS` dict in `services/users.py`; only code in that file may read or write `USERS` (CLAUDE.md, Architecture).
- All routes live in one file, `routes/api.py`. There is no `routes/users.py`.
- `GET /users/<id>` exists. **There is no user list endpoint**, so SA-1 adds `list_users()` and SA-3 adds `GET /users`.
- `tests/conftest.py` only restores `TASKS` between tests, not `USERS`.

## Pipeline
SA-1 data → SA-2 service → SA-3 API → SA-4 tests. Each one runs in a fresh session (`/clear`), with the prompt below pasted unchanged. After each one: `git diff --stat`, `/usr/bin/python3 -m pytest -q`, and a commit.

---

### SA-1: Data layer
- **Input:** `services/users.py`, `CLAUDE.md`
- **Task:** Add the nullable `notification_pref` field to every user record and add a `list_users()` read function.
- **Output:** `services/users.py` only
- **Constraints:**
  - Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, or anything in `tests/`.
  - Do not create `services/notifications.py` or any other new file.
  - Do not add any get/update function for notification preferences.
  - Do not change the signatures of `get_user` or `create_user`, and keep seed ids 1 and 2.
- **Hand-off to SA-2:** field name `notification_pref`; `None` means "not set" and is reported as `"none"`; the constant `NOTIFICATION_PREFS = ("email", "sms", "none")` in `services/users.py`; `list_users() -> list[dict]`.

**Prompt (paste unchanged):**
```
You are SA-1 (data layer) for a notification-preference feature.
Input: services/users.py and CLAUDE.md.
Task: In services/users.py only:
1. Add the constant NOTIFICATION_PREFS = ("email", "sms", "none").
2. Add "notification_pref": None to both seed records in USERS (None means "not set").
3. Make create_user store "notification_pref": None on new users. Do not change its signature.
4. Add list_users() -> list[dict] that returns all user records, with a Google-style
   docstring like get_user.
Constraints:
- Do not touch routes/api.py, services/tasks.py, utils/errors.py, or any file in tests/.
- Do not create services/notifications.py or any other new file.
- Do not add any function that reads or updates the notification preference.
- Keep seed ids 1 and 2 and all existing fields.
When done, run /usr/bin/python3 -m pytest -q and paste the full output.
Follow CLAUDE.md.
```

---

### SA-2: Service layer
- **Input:** `services/users.py` (as left by SA-1), `utils/errors.py`, `CLAUDE.md`
- **Task:** Create `services/notifications.py` with functions to read and update a user's notification preference.
- **Output:** new file `services/notifications.py` only
- **Constraints:**
  - Do not touch `services/users.py`, `routes/api.py`, `services/tasks.py`, `utils/errors.py`, or anything in `tests/`.
  - Do not import `USERS`; go through `get_user()` (CLAUDE.md cross-service rule).
  - Do not write routes or HTTP responses.
- **Hand-off to SA-3:** `get_notification_pref(user_id: int) -> dict` returns `{"user_id": id, "notification_pref": "<value>"}` (`None` is reported as `"none"`); `update_notification_pref(user_id: int, pref: str) -> dict` returns the same shape. Both raise `NotFoundError("User")` (404) for an unknown user; the update raises `ValidationError("notification_pref", ...)` (422) for a value not in `NOTIFICATION_PREFS`.

**Prompt (paste unchanged):**
```
You are SA-2 (service layer) for a notification-preference feature.
Input: services/users.py (it already has NOTIFICATION_PREFS, a nullable
"notification_pref" field on every user, get_user and list_users), utils/errors.py, CLAUDE.md.
Task: Create a new file services/notifications.py with:
- get_notification_pref(user_id: int) -> dict
  returns {"user_id": user_id, "notification_pref": value}; a stored None is returned as "none".
- update_notification_pref(user_id: int, pref: str) -> dict
  rejects any value not in NOTIFICATION_PREFS with ValidationError("notification_pref", ...),
  stores it on the user record, and returns the same shape as get_notification_pref.
Both raise NotFoundError("User") for an unknown user by calling get_user(user_id).
Use type hints and Google-style docstrings like services/users.py.
Constraints:
- services/notifications.py is the only file you may create or edit.
- Do not touch services/users.py, routes/api.py, services/tasks.py, utils/errors.py, or any file in tests/.
- Do not import USERS; read and update the user through the dict returned by get_user().
- Do not write routes or HTTP responses.
When done, run /usr/bin/python3 -m pytest -q and paste the full output.
Follow CLAUDE.md.
```

---

### SA-3: API layer
- **Input:** `routes/api.py`, `services/notifications.py`, `services/users.py`, `CLAUDE.md`
- **Task:** Expose the notification endpoints and a user list endpoint in `routes/api.py`.
- **Output:** `routes/api.py` only
- **Constraints:**
  - Do not touch anything in `services/`, `utils/errors.py`, or anything in `tests/`.
  - No validation or business logic in routes: parse the request, call one service function, return `jsonify(...)`.
  - Do not change the existing task routes.
- **Hand-off to SA-4:** `GET /api/users` → 200 list (each item has `notification_pref`); `GET /api/users/<id>` → 200 user with `notification_pref` (may be `null`); `GET /api/users/<id>/notifications` → 200 `{"user_id", "notification_pref"}`; `PATCH /api/users/<id>/notifications` with `{"notification_pref": "email"}` → 200; invalid value → 422; unknown user → 404; empty or non-JSON body → 422.

**Prompt (paste unchanged):**
```
You are SA-3 (API layer) for a notification-preference feature.
Input: routes/api.py, services/notifications.py (get_notification_pref(user_id) and
update_notification_pref(user_id, pref), which raise NotFoundError / ValidationError),
services/users.py (list_users()), CLAUDE.md.
Task: In routes/api.py only, add:
- GET /users -> jsonify(list_users())
- GET /users/<int:user_id>/notifications -> jsonify(get_notification_pref(user_id))
- PATCH /users/<int:user_id>/notifications -> read the body with
  request.get_json(silent=True) or {}, pass data.get("notification_pref") to
  update_notification_pref, return jsonify(result)
The existing GET /users/<int:user_id> already returns the stored record, which now
includes notification_pref; leave it as is.
Constraints:
- routes/api.py is the only file you may edit.
- Do not touch any file in services/, utils/errors.py, or any file in tests/.
- No validation or business logic in routes: parse, call one service function, jsonify.
- Do not change the existing task routes.
When done, run /usr/bin/python3 -m pytest -q and paste the full output.
Follow CLAUDE.md.
```

---

### SA-4: Tests
- **Input:** `services/users.py`, `services/notifications.py`, `routes/api.py`, `tests/conftest.py`, `tests/test_api.py` (for the `client` fixture pattern), `CLAUDE.md`
- **Task:** Write service and API tests for the notification feature and isolate `USERS` between tests.
- **Output:** new `tests/test_notifications.py`; `tests/conftest.py` (add a `USERS` snapshot/restore)
- **Constraints:**
  - Do not touch any file outside `tests/`: no `services/`, `routes/`, `utils/`, `app.py`.
  - Do not edit `tests/test_tasks.py` or `tests/test_api.py`.
  - If a test fails because of production code, stop and report it; do not change production code.
- **Hand-off:** final `pytest -q` output for the feature; any production bug found goes into `## Divergence`.

**Prompt (paste unchanged):**
```
You are SA-4 (tests) for a notification-preference feature.
Input: services/users.py, services/notifications.py, routes/api.py,
tests/conftest.py, tests/test_api.py (copy its client fixture pattern), CLAUDE.md.
Behavior to test:
- get_notification_pref / update_notification_pref: default "none" for seed users;
  "email", "sms", "none" accepted; invalid values (e.g. "fax", "", None) raise
  ValidationError; unknown user raises NotFoundError.
- GET /api/users -> 200 list, each item has notification_pref.
- GET /api/users/1 -> includes notification_pref.
- GET /api/users/1/notifications -> 200 {"user_id": 1, "notification_pref": "none"}.
- PATCH /api/users/1/notifications {"notification_pref": "sms"} -> 200, and a
  following GET returns "sms"; invalid value -> 422; unknown user -> 404;
  empty or non-JSON body -> 422.
Task:
1. Create tests/test_notifications.py with these tests, asserting specific error
   classes (pytest.raises(ValidationError), not Exception).
2. In tests/conftest.py, extend the autouse fixture so USERS is deep-copied before
   each test and restored after, the same way TASKS is.
Constraints:
- Only tests/test_notifications.py and tests/conftest.py may be created or edited.
- Do not touch services/, routes/, utils/, app.py, tests/test_tasks.py or tests/test_api.py.
- If a test fails because of production code, stop and report it. Do not fix production code.
When done, run /usr/bin/python3 -m pytest -q and paste the full output.
Follow CLAUDE.md.
```

---

## Recovery subagents (written after SA-4, not part of the original plan)
SA-4 exposed a mismatch the original hand-offs did not cover (see Divergence 2). I fixed it with two more single-layer subagents, each in a fresh session, rather than one session editing both layers.

**SA-1b prompt:**
```
You are SA-1b (data-layer fix). Problem found after SA-4: GET /api/users/1 returns
"notification_pref": null while GET /api/users/1/notifications returns "none".
Task: In services/users.py only, store the default "none" instead of None for both
seed users and in create_user, so every endpoint shows "none". The field stays
nullable (do not reject None elsewhere).
Constraints:
- services/users.py is the only file you may edit.
- Do not touch services/notifications.py, routes/api.py, or any file in tests/.
When done, run /usr/bin/python3 -m pytest -q and paste the full output.
Follow CLAUDE.md.
```

**SA-4b prompt:**
```
You are SA-4b (test fix). The notification tests only check that the
notification_pref key exists on GET /api/users and GET /api/users/1, so a null
value passed. In tests/test_notifications.py only, make those tests assert the
value is "none" for seed users.
Constraints:
- tests/test_notifications.py is the only file you may edit.
- Do not touch services/, routes/, or any other test file.
When done, run /usr/bin/python3 -m pytest -q and paste the full output.
```

## Execution log
Filled in after each subagent: fresh session, `git diff --stat`, `pytest -q` output.

| SA | Fresh session? | Files actually changed (`git diff --stat`) | `pytest -q` | Constraint kept? / fixes in same session |
|---|---|---|---|---|
| SA-1 | Yes (`/clear`) | `services/users.py` only (+18 / −3): `NOTIFICATION_PREFS`, `"notification_pref": None` on both seeds and in `create_user`, new `list_users()` | `75 passed` (unchanged; no new tests in this layer) | Yes. No new file, no notification get/update function, `get_user`/`create_user` signatures unchanged. No fixes needed. |
| SA-2 | Yes (`/clear`) | new `services/notifications.py` only; `services/users.py` untouched | `75 passed` (unchanged; no new tests in this layer) | Yes. Imports only `NOTIFICATION_PREFS` and `get_user` (no `USERS`), updates through the dict `get_user()` returns, no routes. First attempt: Claude sent the `Write` of `services/notifications.py` and a `Bash` smoke test + `pytest -q` in parallel, although the test depended on the file; I interrupted, which rejected both, and re-pasted the same prompt in the same session. It then said "I ran the test command in parallel with the file write it depended on" and did them one at a time. Spot check: `update_notification_pref(1, "fax")` / `None` / `""` → `ValidationError`; user 9 → `NotFoundError`. |
| SA-3 | Yes (`/clear`) | `routes/api.py` only (+20 / −1): imports, `GET /users`, `GET` and `PATCH /users/<id>/notifications` | `75 passed` (unchanged; no new tests in this layer) | Yes. Routes only parse and call one service function; task routes unchanged; no files in `services/` or `tests/` touched. Manual check with the test client: PATCH `email` → 200, `fax` / `{}` / non-JSON → 422, user 9 → 404. Found: `GET /api/users/1` returns `"notification_pref": null` while `GET /api/users/1/notifications` returns `"none"` (see Divergence 2). |
| SA-4 | Yes (`/clear`) | new `tests/test_notifications.py` (21 cases); `tests/conftest.py` fixture now restores `USERS` as well as `TASKS` (renamed `restore_tasks` → `restore_data`) | `96 passed` (75 → 96) | Yes. No production file touched. It reported the `null` vs `"none"` mismatch instead of fixing it ("that's a production change in services/users.py and I'd want your go-ahead first"), but its API tests only assert that the `notification_pref` key is present, so the mismatch passes. All new tests passed on the first run, since SA-1–SA-3 had already written the code. |
| SA-1b (recovery) | Yes (`/clear`) | `services/users.py` only (+3 / −3): seeds and `create_user` now store `"none"` instead of `None` | `96 passed` | Yes. Did not touch `services/notifications.py`, `routes/api.py` or `tests/`. |
| SA-4b (recovery) | Yes (`/clear`) | `tests/test_notifications.py` only (+3 / −2): the user list and detail tests now assert `notification_pref == "none"` instead of only checking the key exists | `96 passed` | File boundary kept, but it went beyond the prompt: to prove the new assertions catch the old bug it created a temporary git worktree at commit `059f443` (before SA-1b), ran the tests there (both failed, as expected), then deleted the worktree. Useful evidence, but I never asked it to run git commands. `GET /api/users/1` and `GET /api/users/1/notifications` now both return `"none"`. |

## Divergence
1. **Did Claude violate any constraint? Which one, and what did it do instead?**
   No file boundary was crossed. After each subagent, `git diff --stat` and the commit showed only the files in its Output field: SA-1 `services/users.py`, SA-2 the new `services/notifications.py`, SA-3 `routes/api.py`, SA-4 `tests/test_notifications.py` + `tests/conftest.py`, SA-1b `services/users.py`, SA-4b `tests/test_notifications.py`. I also searched the six Task 2 session transcripts for rejected tool calls: the only two were in SA-2, where Claude sent the `Write` for `services/notifications.py` and a `Bash` smoke test + `pytest -q` at the same time, although the test needed the file; I interrupted, and it redid them one at a time. That is a sequencing mistake, not a boundary violation.
   The closest thing to a violation was SA-4: its own tests exposed the `null` / `"none"` mismatch, the fix was in `services/users.py`, and it stopped and asked ("that's a production change in services/users.py and I'd want your go-ahead first") instead of editing it. Three actions went beyond the prompts without touching a forbidden file: SA-4 renamed the conftest fixture `restore_tasks` → `restore_data` (I only asked it to extend it); SA-4b created and deleted a temporary git worktree at commit `059f443` to show its new assertions fail on the old code (I never asked for git commands); and SA-4 opened with "your usual workflow is to show tests failing before implementing", a preference I only stated in Task 1, so it reached a `/clear`ed session through Claude's saved memory. My constraints only named files, so none of these was technically a violation, which is itself the gap.

2. **Did any subagent's output break the next subagent's assumptions? How did you recover?**
   Yes. SA-1 stored `"notification_pref": None` as my prompt said ("None means not set"). SA-2 translated `None` to `"none"` in `get_notification_pref`. SA-3 was told the existing `GET /users/<id>` "already returns the stored record", so it returned it raw. Result: `GET /api/users/1` gave `null` while `GET /api/users/1/notifications` gave `"none"` for the same user. Each subagent followed its own prompt; the "report `None` as `"none"`" rule was only in the SA-1 → SA-2 hand-off and never reached SA-3. SA-4 noticed it but, following "do not fix production code", only reported it, and its API tests asserted just that the key exists, so `pytest -q` stayed green (96 passed) with the bug in place. Recovery, keeping the layer split: SA-1b (fresh session, `services/users.py` only) changed the stored default to `"none"`; SA-4b (fresh session, `tests/test_notifications.py` only) made the user list and detail tests assert the value `"none"`. Still 96 passed, and both endpoints now agree.

3. **What would you change about the decomposition next time?**
   - Put the external contract in every hand-off, not just the next one: one line copied into SA-1 through SA-4 such as "every endpoint shows `notification_pref` as `email`/`sms`/`none`, never `null`". The bug came from a convention that lived in a single hand-off.
   - Don't store a sentinel the API must translate: SA-1 should have stored `"none"` from the start, which makes SA-2's `None → "none"` mapping unnecessary.
   - Move tests to the front: an SA-0 that writes the acceptance tests from the feature spec, before any code, so later subagents go from red to green. SA-4 wrote its tests after reading the implementation, which is why it asserted "key present" instead of the specified value.
   - Constrain actions, not just files: add "no git commands, no renaming existing names, run only `/usr/bin/python3 -m pytest -q`" to every prompt. My constraints only listed files, so SA-4b's worktree and SA-4's fixture rename were allowed by the letter of the prompt.
   - Treat Claude's memory as context that survives `/clear`: check or clear saved memories between subagents, or tell each one to ignore them.
