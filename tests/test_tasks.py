import pytest
from services.tasks import process_order, get_task, create_task
from services.tasks import get_tasks_for_user, update_task, TASKS
from services.tasks import list_tasks
from utils.errors import NotFoundError, ValidationError

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(Exception):
        get_task(999)


def test_get_task_not_found_raises_not_found_error():
    with pytest.raises(NotFoundError):
        get_task(999)


def test_create_task_valid():
    result = create_task("Plan trip", 1)
    assert result["title"] == "Plan trip"
    assert result["done"] is False


def test_get_tasks_for_user_valid():
    result = get_tasks_for_user(1)
    ids = {task["id"] for task in result}
    assert {1, 2} <= ids
    assert 3 not in ids
    assert all(task["user_id"] == 1 for task in result)


def test_get_tasks_for_user_not_found_raises_not_found_error():
    with pytest.raises(NotFoundError):
        get_tasks_for_user(999)


def test_create_task_default_priority():
    result = create_task("Plan trip", 1)
    assert result["priority"] == 3


@pytest.mark.parametrize("priority", [1, 5])
def test_create_task_with_priority(priority):
    result = create_task("Plan trip", 1, priority=priority)
    assert result["priority"] == priority


@pytest.mark.parametrize("priority", [0, 6, -1])
def test_create_task_priority_out_of_range_raises_validation_error(priority):
    with pytest.raises(ValidationError):
        create_task("Plan trip", 1, priority=priority)


@pytest.mark.parametrize("priority", ["3", 3.0, True])
def test_create_task_priority_non_int_raises_validation_error(priority):
    with pytest.raises(ValidationError):
        create_task("Plan trip", 1, priority=priority)


def test_create_task_invalid_priority_not_stored():
    count = len(TASKS)
    with pytest.raises(ValidationError):
        create_task("Plan trip", 1, priority=0)
    assert len(TASKS) == count


@pytest.mark.parametrize("title", [None, "", "   ", 123])
def test_create_task_invalid_title_raises_validation_error(title):
    with pytest.raises(ValidationError):
        create_task(title, 1)


@pytest.mark.parametrize("user_id", [None, "1", True])
def test_create_task_invalid_user_id_raises_validation_error(user_id):
    with pytest.raises(ValidationError):
        create_task("Plan trip", user_id)


def test_create_task_unknown_user_raises_not_found_error():
    with pytest.raises(NotFoundError):
        create_task("Plan trip", 999)


def test_create_task_invalid_title_not_stored():
    count = len(TASKS)
    with pytest.raises(ValidationError):
        create_task(None, 1)
    assert len(TASKS) == count


def test_create_task_unknown_user_not_stored():
    count = len(TASKS)
    with pytest.raises(NotFoundError):
        create_task("Plan trip", 999)
    assert len(TASKS) == count


def test_seed_tasks_have_priority():
    for task_id in (1, 2, 3):
        assert 1 <= TASKS[task_id]["priority"] <= 5


def test_update_task_priority():
    task = create_task("Plan trip", 1)
    result = update_task(task["id"], priority=1)
    assert result["priority"] == 1
    assert TASKS[task["id"]]["priority"] == 1
    assert result["title"] == "Plan trip"
    assert result["done"] is False


def test_update_task_title():
    task = create_task("Plan trip", 1, priority=2)
    result = update_task(task["id"], title="Book flights")
    assert result["title"] == "Book flights"
    assert result["priority"] == 2
    assert result["done"] is False


def test_update_task_done():
    task = create_task("Plan trip", 1, priority=2)
    result = update_task(task["id"], done=True)
    assert result["done"] is True
    assert result["title"] == "Plan trip"
    assert result["priority"] == 2


def test_update_task_not_found_raises_not_found_error():
    with pytest.raises(NotFoundError):
        update_task(999, priority=1)


@pytest.mark.parametrize("priority", [0, 6, "3", True])
def test_update_task_invalid_priority_raises_validation_error(priority):
    task = create_task("Plan trip", 1)
    with pytest.raises(ValidationError):
        update_task(task["id"], priority=priority)


@pytest.mark.parametrize("title", ["", "   "])
def test_update_task_empty_title_raises_validation_error(title):
    task = create_task("Plan trip", 1)
    with pytest.raises(ValidationError):
        update_task(task["id"], title=title)


@pytest.mark.parametrize("done", ["yes", 1])
def test_update_task_non_bool_done_raises_validation_error(done):
    task = create_task("Plan trip", 1)
    with pytest.raises(ValidationError):
        update_task(task["id"], done=done)


def test_update_task_invalid_field_leaves_task_unchanged():
    task = create_task("Plan trip", 1)
    with pytest.raises(ValidationError):
        update_task(task["id"], title="New", priority=0)
    assert TASKS[task["id"]]["title"] == "Plan trip"
    assert TASKS[task["id"]]["priority"] == 3


def test_update_task_no_fields_raises_validation_error():
    task = create_task("Plan trip", 1)
    with pytest.raises(ValidationError):
        update_task(task["id"])


def test_tasks_restored_between_tests():
    # test_process_order_valid marks task 1 done; the conftest fixture
    # must have restored it.
    assert TASKS[1]["done"] is False


def test_list_tasks_returns_all():
    result = list_tasks()
    ids = {task["id"] for task in result}
    assert {1, 2, 3} <= ids
    assert len(result) == len(TASKS)


def test_list_tasks_filter_by_priority():
    task = create_task("Plan trip", 1, priority=1)
    result = list_tasks(1)
    ids = {t["id"] for t in result}
    assert task["id"] in ids
    assert all(t["priority"] == 1 for t in result)
    assert not ids & {1, 2, 3}


def test_list_tasks_filter_by_priority_no_match_returns_empty():
    assert list_tasks(5) == []


@pytest.mark.parametrize("priority", [0, 6, "3", True])
def test_list_tasks_filter_by_priority_invalid_raises_validation_error(
        priority):
    with pytest.raises(ValidationError):
        list_tasks(priority)
