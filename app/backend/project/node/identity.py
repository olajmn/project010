"""
A node's identity: how its id is made and how it is shown. Every node id
is minted here and nowhere else. Why ids look like this, and the rules
they keep: README.md in this folder and docs/05-decisions.md #78.
"""

import uuid

# As many characters as people see, like a short git commit id.
SHORT_LENGTH = 8


def new_node_id() -> str:
    """A new node id: a random UUIDv4 in its standard written form. Unique
    beyond this project and this app, and it says nothing about when the
    node was made or how many came before it."""
    return str(uuid.uuid4())


def short_id(node_id: str) -> str:
    """The id as shown to people: its first SHORT_LENGTH characters."""
    return node_id[:SHORT_LENGTH]
