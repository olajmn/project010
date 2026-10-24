"""
Every id the app makes, made here and nowhere else. An id is a random
UUIDv4 and says nothing else, not even what it belongs to: that is
known from where it is kept. Each function's name says what it makes.
What ids promise and why they look like this: README.md in this folder.
"""

import uuid

# As many characters as people see, like a short git commit id.
SHORT_LENGTH = 8


def new_node_id() -> str:
    """A map node's id."""
    return _new()


def new_change_id() -> str:
    """A change record's id (project/changes/records.py)."""
    return _new()


def new_project_id() -> str:
    """A project's id; also its folder name under data/projects/."""
    return _new()


def new_account_id() -> str:
    """An account's id."""
    return _new()


def short_id(an_id: str) -> str:
    """The id as shown to people: its first SHORT_LENGTH characters."""
    return an_id[:SHORT_LENGTH]


def _new() -> str:
    return str(uuid.uuid4())
