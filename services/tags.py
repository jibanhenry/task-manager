from schemas.tags import FIELDS
from utils.errors import ValidationError

TAGS: dict[int, dict] = {}


def create_tag(name: str) -> dict:
    """Create a new tag.

    Args:
        name: The tag's display name.

    Returns:
        The newly created tag record.

    Raises:
        ValidationError: If name is missing or empty.
    """
    if not name or not isinstance(name, str) or not name.strip():
        raise ValidationError("name", "cannot be empty")
    new_id = max(TAGS, default=0) + 1
    record = {"id": new_id, "name": name.strip()}
    TAGS[new_id] = {key: record[key] for key in FIELDS}
    return TAGS[new_id]


def list_tags() -> list[dict]:
    """Retrieve all tags.

    Returns:
        A list of all tag records as dictionaries.
    """
    return list(TAGS.values())
