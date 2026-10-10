import copy

import pytest

from services.tasks import TASKS
from services.users import USERS


@pytest.fixture(autouse=True)
def restore_data():
    """Snapshot TASKS and USERS before each test and restore them afterwards.

    Both dicts are mutated in place because routes and services hold
    references to the same dict objects.
    """
    saved_tasks = copy.deepcopy(TASKS)
    saved_users = copy.deepcopy(USERS)
    yield
    TASKS.clear()
    TASKS.update(saved_tasks)
    USERS.clear()
    USERS.update(saved_users)
