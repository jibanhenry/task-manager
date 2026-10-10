import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_post_task_with_priority(client):
    resp = client.post("/api/tasks",
                       json={"title": "Plan trip", "user_id": 1,
                             "priority": 1})
    assert resp.status_code == 201
    assert resp.get_json()["priority"] == 1


def test_post_task_default_priority(client):
    resp = client.post("/api/tasks", json={"title": "Plan trip", "user_id": 1})
    assert resp.status_code == 201
    assert resp.get_json()["priority"] == 3


def test_post_task_invalid_priority_returns_422(client):
    resp = client.post("/api/tasks",
                       json={"title": "Plan trip", "user_id": 1,
                             "priority": 0})
    assert resp.status_code == 422
    assert "error" in resp.get_json()


def test_get_task_includes_priority(client):
    resp = client.get("/api/tasks/1")
    assert resp.status_code == 200
    assert "priority" in resp.get_json()


def test_patch_task_updates_fields(client):
    created = client.post("/api/tasks",
                          json={"title": "Plan trip", "user_id": 1})
    task_id = created.get_json()["id"]
    resp = client.patch(f"/api/tasks/{task_id}",
                        json={"priority": 2, "done": True, "title": "X"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["priority"] == 2
    assert body["done"] is True
    assert body["title"] == "X"


def test_patch_task_not_found_returns_404(client):
    resp = client.patch("/api/tasks/999", json={"priority": 2})
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_patch_task_invalid_priority_returns_422(client):
    resp = client.patch("/api/tasks/1", json={"priority": 9})
    assert resp.status_code == 422
    assert "error" in resp.get_json()


@pytest.mark.parametrize("kwargs", [
    {},
    {"data": "not json", "content_type": "text/plain"},
    {"json": {}},
])
def test_patch_task_empty_or_non_json_body_returns_422(client, kwargs):
    resp = client.patch("/api/tasks/1", **kwargs)
    assert resp.status_code == 422
    assert "error" in resp.get_json()
