"""
Every id the app makes, made here and nowhere else. An id is its kind
and a random UUIDv4: `node_3f9c2a71-8b4e-4d10-a6f2-91c0e7b45d38`. The
rest of the app treats ids as opaque strings; what they promise and why
they look like this: README.md in this folder.
"""

import uuid

# The kinds of id, each a prefix that says what an id belongs to.
NODE = "node"
CHANGE = "change"
PROJECT = "project"
ACCOUNT = "account"
KINDS = (NODE, CHANGE, PROJECT, ACCOUNT)

# As many characters as people see, like a short git commit id.
SHORT_LENGTH = 8


def new_node_id() -> str:
    """A map node's id."""
    return _new(NODE)


def new_change_id() -> str:
    """A change record's id (project/changes/records.py)."""
    return _new(CHANGE)


def new_project_id() -> str:
    """A project's id; also its folder name under data/projects/."""
    return _new(PROJECT)


def new_account_id() -> str:
    """An account's id."""
    return _new(ACCOUNT)


def kind_of(an_id: str) -> str | None:
    """The kind an id belongs to, or None for an id without one (ids
    made before kinds had a prefix)."""
    prefix, sep, _ = an_id.partition("_")
    return prefix if sep and prefix in KINDS else None


def short_id(an_id: str) -> str:
    """The id as shown to people: SHORT_LENGTH characters after its kind."""
    kind = kind_of(an_id)
    rest = an_id[len(kind) + 1 :] if kind else an_id
    return rest[:SHORT_LENGTH]


def _new(kind: str) -> str:
    return f"{kind}_{uuid.uuid4()}"
