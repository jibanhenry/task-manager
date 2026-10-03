TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2},
}

def process_order(task_id: int) -> dict:
    task = TASKS[task_id]
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    return TASKS[task_id]

def create_task(title: str, user_id: int) -> dict:
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id}
    return TASKS[new_id]
