import pytest
from services.tasks import process_order, get_task, create_task
from utils.errors import NotFoundError

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
