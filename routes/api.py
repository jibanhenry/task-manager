from flask import Blueprint, jsonify, request
from services.tasks import get_task, create_task, process_order
from services.tasks import update_task, list_tasks
from services.users import get_user
from utils.errors import AppError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code


@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    priority = request.args.get("priority")
    if priority is not None and priority.isdigit():
        priority = int(priority)
    return jsonify(list_tasks(priority))


@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json(silent=True) or {}
    return jsonify(create_task(data.get("title"), data.get("user_id"),
                               data.get("priority", 3))), 201


@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    data = request.get_json(silent=True) or {}
    return jsonify(update_task(task_id, data.get("title"),
                               data.get("done"), data.get("priority")))


@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))
