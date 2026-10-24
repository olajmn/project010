"""
Change records: what one map edit did, saved with it in events.jsonl so
the edit can be replayed, reversed, or described in full (TODO.md 54).
A record names nodes by id and holds whole nodes, never only labels.

Every record has its own `id` (a `change_…` id from backend/identity/),
so an undo can name the change it reverses. Shapes, by `op`:
- add: `parent` (its id, None at the top), `index` (place of the first
  node among its siblings), `nodes` (every node added, whole, with ids).
- remove: `parent`, `index`, `nodes` (the removed node and all under it;
  the same shape as add, so each is the other's reverse).
- move: `node_id`, `parent`, `from`, `to` (places among its siblings).
- rename: `node_id`, `from`, `to` (labels).

An undo saves the reverse of a change with `undoes` (that change's id);
a redo saves the change again with `redoes` (changes/undo.py).

Nodes are copied, so a record stays what happened even if the tree it
came from changes later.
"""

import copy

from backend.identity import new_change_id


def added(parent_id: str | None, index: int, nodes: list[dict]) -> dict:
    return {
        "id": new_change_id(),
        "op": "add",
        "parent": parent_id,
        "index": index,
        "nodes": copy.deepcopy(nodes),
    }


def removed(parent_id: str | None, index: int, nodes: list[dict]) -> dict:
    return {
        "id": new_change_id(),
        "op": "remove",
        "parent": parent_id,
        "index": index,
        "nodes": copy.deepcopy(nodes),
    }


def moved(step_id: str, parent_id: str | None, from_index: int, to_index: int) -> dict:
    return {
        "id": new_change_id(),
        "op": "move",
        "node_id": step_id,
        "parent": parent_id,
        "from": from_index,
        "to": to_index,
    }


def renamed(step_id: str, old: str, new: str) -> dict:
    return {
        "id": new_change_id(),
        "op": "rename",
        "node_id": step_id,
        "from": old,
        "to": new,
    }


# Each op and the op that reverses it.
_REVERSE_OP = {"add": "remove", "remove": "add", "move": "move", "rename": "rename"}


def reversed_change(change: dict) -> dict:
    """A new record that undoes `change`: add and remove swap, a move
    and a rename swap `from` and `to`."""
    out = _fresh_copy(change)
    out["op"] = _REVERSE_OP[change["op"]]
    if change["op"] in ("move", "rename"):
        out["from"], out["to"] = change["to"], change["from"]
    out["undoes"] = change["id"]
    return out


def repeated_change(change: dict) -> dict:
    """A new record that does `change` again (a redo)."""
    out = _fresh_copy(change)
    out["redoes"] = change["id"]
    return out


def _fresh_copy(change: dict) -> dict:
    """`change` copied with a new id and without its undo/redo link."""
    out = {
        key: copy.deepcopy(value)
        for key, value in change.items()
        if key not in ("undoes", "redoes")
    }
    out["id"] = new_change_id()
    return out
