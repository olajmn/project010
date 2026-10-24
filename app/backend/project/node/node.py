"""
One project node: the recursive Node shape at every depth of the
family tree (parent/child). The atom the rest of the system builds from.

Depth is data, not type — where a node sits in the tree, not what
class it is (project/node/README.md).

Pure shape — no model call, no persistence. Stored as the record's
`nodes`. Canvas/chat are faces of nodes; they do not own the shape.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Node:
    """One position in the project's node tree."""

    # Minted once and never reused, so a node can change without
    # becoming a different node. Display numbering ("1.", "i.") is
    # computed from sibling position at render time and deliberately
    # not stored here.
    id: str
    label: str
    children: list[Node] = field(default_factory=list)

    # Absolute path when this node was minted from a file or folder.
    # Absent on nodes the user typed or pasted.
    path: str | None = None

    # Whether the children have to happen in order.
    ordered: bool = True

    # Whether this node's claim is realized.
    resolved: bool = False

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "label": self.label,
            "ordered": self.ordered,
            "resolved": self.resolved,
            "children": [child.to_dict() for child in self.children],
        }
        if self.path:
            data["path"] = self.path
        return data


def nodes_of(record: dict) -> list:
    """The top-level nodes stored on a project record (`nodes`), or []
    when there are none. The one place that knows where nodes sit on a
    record."""
    nodes = record.get("nodes")
    return nodes if isinstance(nodes, list) else []


def count_nodes(nodes: list) -> int:
    """Every node in `nodes` and under them, at any depth."""
    return sum(
        1 + count_nodes(s.get("children") or []) for s in nodes if isinstance(s, dict)
    )


def sibling_label_clash(siblings: list, label: str) -> str | None:
    """If a sibling already uses this label (same level), return an
    error string; else None. Accepts Node objects or dict nodes."""
    wanted = (label or "").strip()
    if not wanted:
        return None
    for sib in siblings or []:
        if isinstance(sib, Node):
            existing = (sib.label or "").strip()
        elif isinstance(sib, dict):
            existing = (sib.get("label") or "").strip()
        else:
            continue
        if existing == wanted:
            return f'A sibling already named "{wanted}".'
    return None


_NUMBERED = re.compile(r"^(.*\S) \((\d+)\)$")


def unique_sibling_label(siblings: list, label: str) -> str:
    """`label`, or `label (2)`, `label (3)`, … — the first form no
    sibling at this level already uses. Accepts Node objects or dict
    nodes.

    Identity is the id (docs/05-decisions.md #52); unique sibling labels
    only keep name paths (`/add`, `/select`) unambiguous and let people
    and the model tell siblings apart. So a clash is resolved, not
    refused. A label that already ends in ` (N)` counts on from N.
    """
    wanted = (label or "").strip()
    if not wanted or not sibling_label_clash(siblings, wanted):
        return wanted
    numbered = _NUMBERED.match(wanted)
    base, n = (numbered.group(1), int(numbered.group(2))) if numbered else (wanted, 1)
    while True:
        n += 1
        candidate = f"{base} ({n})"
        if not sibling_label_clash(siblings, candidate):
            return candidate


def structure_of(node: dict) -> dict:
    """A stored node dict as bare structure: label, order, children.

    Deliberately drops `id` (identity stays with the original node —
    docs/05-decisions.md #52), `resolved` (state, not structure; a copy
    starts unresolved), and `path` (points at one file on one disk).
    The result is the same {"label", "children"} forest shape Paste
    imports, plus `ordered`.
    """
    return {
        "label": str(node.get("label") or ""),
        "ordered": bool(node.get("ordered", True)),
        "children": [
            structure_of(child)
            for child in node.get("children") or []
            if isinstance(child, dict)
        ],
    }


def from_nested_labels(entries: list[dict], mint_id: Callable[[], str]) -> list[Node]:
    """Build nodes from a nested [{"label", "children": [...]}] list,
    recursing to whatever depth that list actually has. Copies `path`
    when present (folder walk) and `ordered` when present (saved tree).

    `mint_id` makes each new id; callers pass backend.identity's
    new_node_id, the one place node ids are made.
    """
    nodes: list[Node] = []
    for entry in entries:
        path = entry.get("path")
        nodes.append(
            Node(
                id=mint_id(),
                label=entry["label"],
                path=path if isinstance(path, str) and path else None,
                ordered=bool(entry.get("ordered", True)),
                children=from_nested_labels(entry.get("children", []), mint_id),
            )
        )
    return nodes
