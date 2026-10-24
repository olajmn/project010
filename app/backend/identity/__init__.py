"""Identity — every id the app makes, in one place (ids.py), apart from
the rest of the system: nodes, change records, and later projects and
accounts. What an id promises: README.md here.
"""

from backend.identity.ids import kind_of, new_change_id, new_node_id, short_id

__all__ = ["kind_of", "new_change_id", "new_node_id", "short_id"]
