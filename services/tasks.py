from services.users import get_user
from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1,
        "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1,
        "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2,
        "priority": 3},
}

def process_order(task_id: int) -> dict:
    task = TASKS[task_id]
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]


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


def create_task(title: str, user_id: int, priority: int = 3) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The ID of the user who owns the task.
        priority: The task's priority from 1 (most urgent) to 5. Defaults
            to 3.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    _validate_priority(priority)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id,
                     "priority": priority}
    return TASKS[new_id]


def get_tasks_for_user(user_id: int) -> list[dict]:
    """Retrieve all tasks owned by a user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A list of the user's task records; empty if the user has no tasks.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    get_user(user_id)
    return [task for task in TASKS.values() if task["user_id"] == user_id]
