from services.users import NOTIFICATION_PREFS, get_user
from utils.errors import ValidationError


def get_notification_pref(user_id: int) -> dict:
    """Retrieve a user's notification preference.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A dictionary with "user_id" and "notification_pref" keys. An unset
        preference is returned as "none".

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    user = get_user(user_id)
    pref = user["notification_pref"]
    return {"user_id": user_id,
            "notification_pref": pref if pref is not None else "none"}


def update_notification_pref(user_id: int, pref: str) -> dict:
    """Update a user's notification preference.

    Args:
        user_id: The unique identifier for the user.
        pref: The new preference; must be one of NOTIFICATION_PREFS.

    Returns:
        A dictionary with "user_id" and "notification_pref" keys.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If pref is not one of NOTIFICATION_PREFS.
    """
    user = get_user(user_id)
    if pref not in NOTIFICATION_PREFS:
        raise ValidationError(
            "notification_pref",
            f"must be one of {', '.join(NOTIFICATION_PREFS)}")
    user["notification_pref"] = pref
    return get_notification_pref(user_id)
