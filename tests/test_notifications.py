import pytest

from app import app
from services.notifications import get_notification_pref
from services.notifications import update_notification_pref
from utils.errors import NotFoundError, ValidationError


@pytest.fixture
def client():
    return app.test_client()


# --- service layer ---

@pytest.mark.parametrize("user_id", [1, 2])
def test_get_notification_pref_defaults_to_none(user_id):
    assert get_notification_pref(user_id) == {
        "user_id": user_id, "notification_pref": "none"}


def test_get_notification_pref_unknown_user_raises_not_found():
    with pytest.raises(NotFoundError):
        get_notification_pref(999)


@pytest.mark.parametrize("pref", ["email", "sms", "none"])
def test_update_notification_pref_accepts_valid_values(pref):
    result = update_notification_pref(1, pref)
    assert result == {"user_id": 1, "notification_pref": pref}
    assert get_notification_pref(1)["notification_pref"] == pref


@pytest.mark.parametrize("pref", ["fax", "", None, "EMAIL"])
def test_update_notification_pref_invalid_raises_validation_error(pref):
    with pytest.raises(ValidationError):
        update_notification_pref(1, pref)
    assert get_notification_pref(1)["notification_pref"] == "none"


def test_update_notification_pref_unknown_user_raises_not_found():
    with pytest.raises(NotFoundError):
        update_notification_pref(999, "email")


# --- API layer ---

def test_get_users_includes_notification_pref(client):
    resp = client.get("/api/users")
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, list)
    assert {1, 2} <= {user["id"] for user in body}
    seed = [user for user in body if user["id"] in (1, 2)]
    assert all(user["notification_pref"] == "none" for user in seed)


def test_get_user_includes_notification_pref(client):
    resp = client.get("/api/users/1")
    assert resp.status_code == 200
    assert resp.get_json()["notification_pref"] == "none"


def test_get_notifications_default(client):
    resp = client.get("/api/users/1/notifications")
    assert resp.status_code == 200
    assert resp.get_json() == {"user_id": 1, "notification_pref": "none"}


def test_get_notifications_unknown_user_returns_404(client):
    resp = client.get("/api/users/999/notifications")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_patch_notifications_updates_pref(client):
    resp = client.patch("/api/users/1/notifications",
                        json={"notification_pref": "sms"})
    assert resp.status_code == 200
    assert resp.get_json() == {"user_id": 1, "notification_pref": "sms"}

    resp = client.get("/api/users/1/notifications")
    assert resp.status_code == 200
    assert resp.get_json()["notification_pref"] == "sms"


def test_patch_notifications_invalid_value_returns_422(client):
    resp = client.patch("/api/users/1/notifications",
                        json={"notification_pref": "fax"})
    assert resp.status_code == 422
    assert "error" in resp.get_json()


def test_patch_notifications_unknown_user_returns_404(client):
    resp = client.patch("/api/users/999/notifications",
                        json={"notification_pref": "sms"})
    assert resp.status_code == 404
    assert "error" in resp.get_json()


@pytest.mark.parametrize("kwargs", [
    {},
    {"data": "not json", "content_type": "text/plain"},
    {"json": {}},
])
def test_patch_notifications_empty_or_non_json_body_returns_422(client,
                                                                kwargs):
    resp = client.patch("/api/users/1/notifications", **kwargs)
    assert resp.status_code == 422
    assert "error" in resp.get_json()
