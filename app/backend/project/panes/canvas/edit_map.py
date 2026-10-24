"""
User-authored writes on a project's nodes (the record's `nodes`). No model.

add_map_node() — one node the user named (no LLM), at the
root or under a parent_id.
import_map_outline() — a whole pasted outline/ASCII tree,
parsed by text_to_tree.py (no LLM), appended the same way.
import_map_folder() — one folder on disk, walked by
add_folder/walk.py, appended the same way. Each node keeps its path.
remove_map_node() — drop a node by id (no LLM).
move_map_node() — swap a node with the sibling above or below it,
keeping its id and everything under it (no LLM).
rename_map_node() — give a node a new label, keeping its id, so chat
turns about it stay attached (docs/05-decisions.md #52, #71).

New nodes get their ids from backend/identity/. Undo and redo are
undo.py, saved through the same save_map_edit().

"""

import copy

from backend.identity import new_node_id
from backend.project.changes import records
from backend.project.node import (
    Node,
    count_nodes,
    find_node,
    find_path,
    from_nested_labels,
    nodes_of,
    sibling_label_clash,
    unique_sibling_label,
)
from backend.project.panes.canvas.add_folder import folder_tree
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.storage.project_persistence import save_project


def add_map_node(
    latest: dict,
    label: str,
    parent_id: str | None = None,
) -> dict:
    """
    Append one node the user named — no model call.
    Empty/whitespace label raises.
    A label a sibling already uses gets ` (2)`, ` (3)`, … appended.
    If parent_id is set, append under that node's children; otherwise
    at the top level.
    """
    text = (label or "").strip()
    if not text:
        raise ValueError("node label is empty")

    tree = copy.deepcopy(nodes_of(latest))

    if parent_id:
        parent = find_node(tree, parent_id)
        if parent is None:
            raise ValueError(f"parent node not found: {parent_id}")
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        siblings = children
    else:
        parent = None
        siblings = tree

    text = unique_sibling_label(siblings, text)

    new_node = Node(id=new_node_id(), label=text).to_dict()
    change = records.added(parent["id"] if parent else None, len(siblings), [new_node])
    siblings.append(new_node)
    if parent is not None:
        feedback = f"Added node under {parent.get('label') or parent_id}: {text}"
    else:
        feedback = f"Added node: {text}"

    return save_map_edit(latest, tree, feedback, "node_added", change)


def import_map_outline(
    latest: dict,
    text: str | None = None,
    parent_id: str | None = None,
    unwrap: bool = True,
    forest: list[dict] | None = None,
    event: str = "pasted",
) -> dict:
    """
    Parse a pasted outline/ASCII tree (parse_outline.py — markdown
    bullets, numbered lists, this app's own box-drawing export, or
    plain lines) and append the whole result as new nodes — no model
    call, same append-not-replace shape as add_map_node().
    Raises ValueError if nothing recognizable parses out, or if
    parent_id is set but not found.

    `unwrap` (default True) matches parse_outline()'s own parameter -
    the caller should offer this as a user choice (see server.py's
    preview route) rather than always accepting the default guess.

    Exactly one of `text` or `forest` is used: `text` is parsed fresh
    (the chat-Send path, which has no preview to edit first);
    `forest` is an already-built {"label", "children"} tree the caller
    supplies directly - ui/'s preview builds one of these by toggling
    individual nodes in/out (see outlinePreviewWithToggleableRoot() /
    applyExclusions() in projects.ts), so what gets imported matches
    exactly what the user saw and chose, not a fresh, unedited
    re-parse of the raw text. `unwrap`/`parse_outline()` do not apply
    to a supplied `forest` - it's already the user's final shape.
    """
    if forest is None:
        forest = parse_outline(text or "", unwrap=unwrap)
    else:
        forest = _validate_forest(forest)
    if not forest:
        raise ValueError("no nodes recognized in that text")

    tree = copy.deepcopy(nodes_of(latest))

    new_nodes = [node.to_dict() for node in from_nested_labels(forest, new_node_id)]
    # Every imported node, not just the top level: one paste of a
    # 95-node tree is one change, but it brought in 95 nodes.
    imported = count_nodes(new_nodes)
    what = "1 node" if imported == 1 else f"{imported} nodes"

    parent = None
    if parent_id:
        parent = find_node(tree, parent_id)
        if parent is None:
            raise ValueError(f"parent node not found: {parent_id}")
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        siblings = children
        feedback = f"Imported {what} under {parent.get('label') or parent_id}"
    else:
        siblings = tree
        feedback = f"Imported {what}"
    _number_sibling_clashes(siblings, new_nodes)
    change = records.added(parent["id"] if parent else None, len(siblings), new_nodes)
    siblings.extend(new_nodes)

    return save_map_edit(latest, tree, feedback, event, change)


def import_map_folder(
    latest: dict,
    folder: str,
    parent_id: str | None = None,
) -> dict:
    """Walk one folder into beads and append them. No model call.
    Same append-not-replace shape as import_map_outline()."""
    return import_map_outline(
        latest,
        parent_id=parent_id,
        forest=folder_tree(folder),
        event="folder_added",
    )


def remove_map_node(latest: dict, node_id: str) -> dict:
    """
    Remove `node_id` (top-level or nested). No model call. Raises if
    the project has no nodes or the node is missing.
    """
    tree = copy.deepcopy(nodes_of(latest))
    if not tree:
        raise ValueError("project has no nodes")

    # Where it sat and how much went with it, read before it is gone.
    path = find_path(tree, node_id)
    if path is None:
        raise ValueError(f"node not found: {node_id}")
    node = path[-1]
    parent = path[-2] if len(path) > 1 else None
    siblings = parent["children"] if parent else tree
    index = next(n for n, s in enumerate(siblings) if s is node)
    change = records.removed(parent["id"] if parent else None, index, [node])
    del siblings[index]
    label = str(node.get("label") or node_id)
    below = count_nodes(node.get("children") or [])
    feedback = (
        f"Removed node under {parent.get('label') or ''}: {label}"
        if parent
        else f"Removed node: {label}"
    )
    if below:
        feedback += f" (and {below} under it)"

    return save_map_edit(latest, tree, feedback, "node_removed", change)


def move_map_node(latest: dict, node_id: str, direction: str) -> dict:
    """
    Move `step_id` one place up or down among its siblings (`direction`
    is "up" or "down"). Same parent, same id, same children - only the
    order changes. No model call. Raises if the node is missing or
    already first/last.
    """
    if direction not in ("up", "down"):
        raise ValueError(f"unknown direction: {direction}")
    tree = copy.deepcopy(nodes_of(latest))
    if not tree:
        raise ValueError("project has no nodes")

    path = find_path(tree, node_id)
    if path is None:
        raise ValueError(f"node not found: {node_id}")
    siblings = path[-2]["children"] if len(path) > 1 else tree
    i = next(n for n, s in enumerate(siblings) if s is path[-1])
    j = i - 1 if direction == "up" else i + 1
    if not 0 <= j < len(siblings):
        raise ValueError(f"already {'first' if direction == 'up' else 'last'}")
    siblings[i], siblings[j] = siblings[j], siblings[i]
    change = records.moved(node_id, path[-2]["id"] if len(path) > 1 else None, i, j)

    # Which neighbour it passed, so Logs and the chat's model can place it.
    label = path[-1].get("label") or node_id
    other = siblings[i].get("label") or ""
    where = "above" if direction == "up" else "below"
    feedback = (
        f"Moved node under {path[-2].get('label') or ''}: {label} {where} {other}"
        if len(path) > 1
        else f"Moved node: {label} {where} {other}"
    )

    return save_map_edit(latest, tree, feedback, "node_moved", change)


def rename_map_node(latest: dict, node_id: str, label: str) -> dict:
    """
    Give `step_id` a new label. Its id, place, and children stay, so
    everything that points at the id (chat turns, selection) still finds
    it. No model call. Raises on an empty label, a missing node, or a
    label a sibling already uses: unlike add, a rename does not number
    itself, since the user chose that exact name.

    The saved line carries the node's id (`focus_step_id`), so the chat
    can show the rename inside that node's conversation.
    """
    text = (label or "").strip()
    if not text:
        raise ValueError("node label is empty")
    tree = copy.deepcopy(nodes_of(latest))
    if not tree:
        raise ValueError("project has no nodes")

    path = find_path(tree, node_id)
    if path is None:
        raise ValueError(f"node not found: {node_id}")
    node = path[-1]
    old = (node.get("label") or "").strip()
    if text == old:
        return latest
    siblings = path[-2]["children"] if len(path) > 1 else tree
    clash = sibling_label_clash([s for s in siblings if s is not node], text)
    if clash:
        raise ValueError(clash)
    node["label"] = text

    return save_map_edit(
        latest,
        tree,
        f"Renamed node: {old} → {text}",
        "node_renamed",
        records.renamed(node_id, old, text),
        focus_node_id=node_id,
    )


def save_map_edit(
    latest: dict,
    tree: list[dict],
    feedback: str,
    event: str,
    change: dict,
    focus_node_id: str | None = None,
) -> dict:
    """Save one map edit: the new tree, its line for Logs and the chat
    (`feedback`), and its full record (`change`, project/changes/). Every
    edit here and every undo and redo (undo.py) saves through this."""
    return save_project(
        latest["name"],
        tree,
        feedback=feedback,
        project_id=latest["project_id"],
        account_id=latest.get("account_id"),
        event=event,
        focus_node_id=focus_node_id,
        change=change,
    )


def _number_sibling_clashes(siblings: list, new_nodes: list[dict]) -> None:
    """Rename in place any new label that collides with existing
    siblings or with an earlier new peer (` (2)`, ` (3)`, …).

    Checks this level against existing siblings, then each new node's
    children among themselves (and so on).
    """
    seen: list = list(siblings)
    for node in new_nodes:
        node["label"] = unique_sibling_label(seen, node.get("label") or "")
        seen.append(node)
        children = node.get("children")
        if isinstance(children, list) and children:
            _number_sibling_clashes([], children)


def _validate_forest(raw: list[dict]) -> list[dict]:
    """A caller-supplied {"label", "children"} tree (ui/'s edited
    preview, not this module's own parse_outline() output) gets the
    same shape check parse_outline() guarantees by construction -
    raises ValueError with a clear reason instead of a raw KeyError/
    TypeError from build() once nesting is already underway."""
    if not isinstance(raw, list):
        raise ValueError("forest must be a list of nodes")
    checked: list[dict] = []
    for node in raw:
        if not isinstance(node, dict):
            raise ValueError("each forest node must be an object")
        label = node.get("label")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("each forest node needs a non-empty label")
        children = node.get("children", [])
        checked_node = {
            "label": label,
            "children": _validate_forest(children),
        }
        path = node.get("path")
        if isinstance(path, str) and path.strip():
            checked_node["path"] = path
        if isinstance(node.get("ordered"), bool):
            checked_node["ordered"] = node["ordered"]
        checked.append(checked_node)
    return checked
