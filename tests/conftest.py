import copy

import pytest

from services.tasks import TASKS


@pytest.fixture(autouse=True)
def restore_tasks():
    """Snapshot TASKS before each test and restore it afterwards.

    TASKS is mutated in place because routes and services hold references
    to the same dict object.
    """
    saved = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(saved)
