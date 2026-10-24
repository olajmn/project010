"""
Change records: what one map edit did, saved with it in events.jsonl so
the edit can be replayed, reversed, or described in full (TODO.md 54).
A record names nodes by id and holds whole nodes, never only labels.

Shapes, by `op`:
- add: `parent` (its id, None at the top), `index` (place of the first
  node among its siblings), `nodes` (every node added, whole, with ids).
- remove: `parent`, `index`, `node` (the removed node and all under it).
- move: `id`, `parent`, `from`, `to` (places among its siblings).
- rename: `id`, `from`, `to` (labels).

Nodes are copied, so a record stays what happened even if the tree it
came from changes later.
"""

import copy


def added(parent_id: str | None, index: int, nodes: list[dict]) -> dict:
    return {
        "op": "add",
        "parent": parent_id,
        "index": index,
        "nodes": copy.deepcopy(nodes),
    }


def removed(parent_id: str | None, index: int, node: dict) -> dict:
    return {
        "op": "remove",
        "parent": parent_id,
        "index": index,
        "node": copy.deepcopy(node),
    }


def moved(step_id: str, parent_id: str | None, from_index: int, to_index: int) -> dict:
    return {
        "op": "move",
        "id": step_id,
        "parent": parent_id,
        "from": from_index,
        "to": to_index,
    }


def renamed(step_id: str, old: str, new: str) -> dict:
    return {"op": "rename", "id": step_id, "from": old, "to": new}
