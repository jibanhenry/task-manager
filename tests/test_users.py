import pytest
from services.users import USERS, get_user, list_users, create_user
from utils.errors import NotFoundError, ValidationError


def test_get_user_valid():
    result = get_user(1)
    assert result == {"id": 1, "name": "Alice", "email": "alice@example.com",
                      "notification_pref": "none"}


def test_get_user_returns_requested_user():
    assert get_user(2)["name"] == "Bob"


@pytest.mark.parametrize("user_id", [0, 3, 999, -1])
def test_get_user_not_found_raises_not_found_error(user_id):
    with pytest.raises(NotFoundError) as exc_info:
        get_user(user_id)
    assert exc_info.value.message == "User not found"
    assert exc_info.value.status_code == 404


def test_list_users_returns_seed_users():
    result = list_users()
    assert isinstance(result, list)
    assert [u["id"] for u in result] == [1, 2]
    assert [u["name"] for u in result] == ["Alice", "Bob"]


def test_list_users_reflects_added_user():
    USERS[3] = {"id": 3, "name": "Carol", "email": "carol@example.com",
                "notification_pref": "none"}
    result = list_users()
    assert len(result) == 3
    assert result[-1]["name"] == "Carol"


def test_list_users_empty_when_no_users():
    USERS.clear()
    assert list_users() == []


def test_create_user_valid():
    result = create_user("Carol", "carol@example.com")
    assert result == {"id": 3, "name": "Carol", "email": "carol@example.com",
                      "notification_pref": "none"}


def test_create_user_is_stored_in_users():
    created = create_user("Carol", "carol@example.com")
    assert get_user(created["id"]) == created
    assert len(list_users()) == 3


def test_create_user_assigns_incrementing_ids():
    first = create_user("Carol", "carol@example.com")
    second = create_user("Dave", "dave@example.com")
    assert first["id"] == 3
    assert second["id"] == 4


@pytest.mark.parametrize("name", ["", "   ", "\t\n", None])
def test_create_user_empty_name_raises_validation_error(name):
    with pytest.raises(ValidationError) as exc_info:
        create_user(name, "carol@example.com")
    assert exc_info.value.message == "Invalid name: cannot be empty"
    assert exc_info.value.status_code == 422


@pytest.mark.parametrize("email", ["", None, "carol.example.com", "   "])
def test_create_user_invalid_email_raises_validation_error(email):
    with pytest.raises(ValidationError) as exc_info:
        create_user("Carol", email)
    assert exc_info.value.message == (
        "Invalid email: must be a valid email address")
    assert exc_info.value.status_code == 422


def test_create_user_invalid_input_does_not_store_user():
    with pytest.raises(ValidationError):
        create_user("", "carol@example.com")
    with pytest.raises(ValidationError):
        create_user("Carol", "not-an-email")
    assert sorted(USERS.keys()) == [1, 2]


@pytest.mark.xfail(
    reason="create_user calls max() on empty USERS, raising a raw ValueError "
           "instead of assigning id 1",
    strict=True)
def test_create_user_when_no_users_exist():
    USERS.clear()
    result = create_user("Carol", "carol@example.com")
    assert result["id"] == 1
