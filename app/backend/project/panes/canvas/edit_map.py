"""
User-authored writes on a project's nodes (plan.progression). No model.

add_map_node() — one Step the user named (no LLM), at the
root or under a parent_id.
import_map_outline() — a whole pasted outline/ASCII tree,
parsed by text_to_tree.py (no LLM), appended the same way.
import_map_folder() — one folder on disk, walked by
add_folder/walk.py, appended the same way. Each node keeps its path.
remove_map_node() — drop a Step by id (no LLM).
move_map_node() — swap a Step with the sibling above or below it,
keeping its id and everything under it (no LLM).
rename_map_node() — give a Step a new label, keeping its id, so chat
turns about it stay attached (docs/05-decisions.md #52, #71).

New nodes get their ids from project/node/identity.py.

Does not touch the Steps-page scratch tree.
"""

import copy

from backend.project.changes import records
from backend.project.node import (
    Step,
    find_path,
    from_nested_labels,
    new_node_id,
    sibling_label_clash,
    unique_sibling_label,
)
from backend.project.panes.canvas.add_folder import folder_tree
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.storage.project_persistence import save_plan


def add_map_node(
    latest: dict,
    label: str,
    parent_id: str | None = None,
) -> dict:
    """
    Append one Step the user named — no model call.
    Creates plan.progression if missing. Empty/whitespace label raises.
    A label a sibling already uses gets ` (2)`, ` (3)`, … appended.
    If parent_id is set, append under that step's children; otherwise
    at the progression root.
    """
    text = (label or "").strip()
    if not text:
        raise ValueError("step label is empty")

    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        progression = {"steps": []}
        plan["progression"] = progression
    steps = progression.get("steps")
    if not isinstance(steps, list):
        steps = []
        progression["steps"] = steps

    if parent_id:
        found = _find_step(steps, parent_id)
        if found is None:
            raise ValueError(f"parent step not found: {parent_id}")
        parent, _ancestors = found
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        siblings = children
    else:
        parent = None
        siblings = steps

    text = unique_sibling_label(siblings, text)

    new_step = Step(id=new_node_id(), label=text).to_dict()
    change = records.added(parent["id"] if parent else None, len(siblings), [new_step])
    siblings.append(new_step)
    if parent is not None:
        feedback = f"Added step under {parent.get('label') or parent_id}: {text}"
    else:
        feedback = f"Added step: {text}"

    return _save_map(latest, plan, feedback, "node_added", change)


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
    plain lines) and append the whole result as new Steps — no model
    call, same append-not-replace shape as add_map_node().
    Raises ValueError if nothing recognizable parses out, or if
    parent_id is set but not found.

    `unwrap` (default True) matches parse_outline()'s own parameter -
    the caller should offer this as a user choice (see server.py's
    preview route) rather than always accepting the default guess.

    Exactly one of `text` or `forest` is used: `text` is parsed fresh
    (the chat-Send path, which has no preview step to edit first);
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
        raise ValueError("no steps recognized in that text")

    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        progression = {"steps": []}
        plan["progression"] = progression
    steps = progression.get("steps")
    if not isinstance(steps, list):
        steps = []
        progression["steps"] = steps

    new_steps = [step.to_dict() for step in from_nested_labels(forest, new_node_id)]
    # Every imported node, not just the top level: one paste of a
    # 95-node tree is one change, but it brought in 95 nodes.
    imported = len(new_steps) + sum(_count_below(s) for s in new_steps)
    what = "1 node" if imported == 1 else f"{imported} nodes"

    parent = None
    if parent_id:
        found = _find_step(steps, parent_id)
        if found is None:
            raise ValueError(f"parent step not found: {parent_id}")
        parent, _ancestors = found
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        siblings = children
        feedback = f"Imported {what} under {parent.get('label') or parent_id}"
    else:
        siblings = steps
        feedback = f"Imported {what}"
    _number_sibling_clashes(siblings, new_steps)
    change = records.added(parent["id"] if parent else None, len(siblings), new_steps)
    siblings.extend(new_steps)

    return _save_map(latest, plan, feedback, event, change)


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


def remove_map_node(latest: dict, step_id: str) -> dict:
    """
    Remove `step_id` from plan.progression (top-level or nested).
    No model call. Raises if missing progression or step.
    """
    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        raise ValueError("project has no nodes")
    steps = progression.get("steps")
    if not isinstance(steps, list):
        raise ValueError("project has no nodes")

    # Where it sat and how much went with it, read before it is gone.
    path = find_path(steps, step_id)
    if path is None:
        raise ValueError(f"step not found: {step_id}")
    step = path[-1]
    parent = path[-2] if len(path) > 1 else None
    siblings = parent["children"] if parent else steps
    index = next(n for n, s in enumerate(siblings) if s is step)
    change = records.removed(parent["id"] if parent else None, index, step)
    del siblings[index]
    label = str(step.get("label") or step_id)
    below = _count_below(step)
    feedback = (
        f"Removed step under {parent.get('label') or ''}: {label}"
        if parent
        else f"Removed step: {label}"
    )
    if below:
        feedback += f" (and {below} under it)"

    if not steps:
        plan["progression"] = None

    return _save_map(latest, plan, feedback, "node_removed", change)


def move_map_node(latest: dict, step_id: str, direction: str) -> dict:
    """
    Move `step_id` one place up or down among its siblings (`direction`
    is "up" or "down"). Same parent, same id, same children - only the
    order changes. No model call. Raises if the step is missing or
    already first/last.
    """
    if direction not in ("up", "down"):
        raise ValueError(f"unknown direction: {direction}")
    plan = copy.deepcopy(latest.get("plan") or {})
    steps = (plan.get("progression") or {}).get("steps")
    if not isinstance(steps, list):
        raise ValueError("project has no nodes")

    path = find_path(steps, step_id)
    if path is None:
        raise ValueError(f"step not found: {step_id}")
    siblings = path[-2]["children"] if len(path) > 1 else steps
    i = next(n for n, s in enumerate(siblings) if s is path[-1])
    j = i - 1 if direction == "up" else i + 1
    if not 0 <= j < len(siblings):
        raise ValueError(f"already {'first' if direction == 'up' else 'last'}")
    siblings[i], siblings[j] = siblings[j], siblings[i]
    change = records.moved(step_id, path[-2]["id"] if len(path) > 1 else None, i, j)

    # Which neighbour it passed, so Logs and the chat's model can place it.
    label = path[-1].get("label") or step_id
    other = siblings[i].get("label") or ""
    where = "above" if direction == "up" else "below"
    feedback = (
        f"Moved step under {path[-2].get('label') or ''}: {label} {where} {other}"
        if len(path) > 1
        else f"Moved step: {label} {where} {other}"
    )

    return _save_map(latest, plan, feedback, "node_moved", change)


def rename_map_node(latest: dict, step_id: str, label: str) -> dict:
    """
    Give `step_id` a new label. Its id, place, and children stay, so
    everything that points at the id (chat turns, selection) still finds
    it. No model call. Raises on an empty label, a missing step, or a
    label a sibling already uses: unlike add, a rename does not number
    itself, since the user chose that exact name.

    The saved line carries the node's id (`focus_step_id`), so the chat
    can show the rename inside that node's conversation.
    """
    text = (label or "").strip()
    if not text:
        raise ValueError("step label is empty")
    plan = copy.deepcopy(latest.get("plan") or {})
    steps = (plan.get("progression") or {}).get("steps")
    if not isinstance(steps, list):
        raise ValueError("project has no nodes")

    path = find_path(steps, step_id)
    if path is None:
        raise ValueError(f"step not found: {step_id}")
    step = path[-1]
    old = (step.get("label") or "").strip()
    if text == old:
        return latest
    siblings = path[-2]["children"] if len(path) > 1 else steps
    clash = sibling_label_clash([s for s in siblings if s is not step], text)
    if clash:
        raise ValueError(clash)
    step["label"] = text

    return _save_map(
        latest,
        plan,
        f"Renamed step: {old} → {text}",
        "node_renamed",
        records.renamed(step_id, old, text),
        focus_step_id=step_id,
    )


def _save_map(
    latest: dict,
    plan: dict,
    feedback: str,
    event: str,
    change: dict,
    focus_step_id: str | None = None,
) -> dict:
    """Save one map edit: the new tree, its line for Logs and the chat
    (`feedback`), and its full record (`change`, project/changes/)."""
    return save_plan(
        latest["name"],
        plan,
        feedback=feedback,
        project_id=latest["project_id"],
        account_id=latest.get("account_id"),
        event=event,
        focus_step_id=focus_step_id,
        change=change,
    )


def _count_below(step: dict) -> int:
    """Every node under `step`, at any depth."""
    children = step.get("children")
    if not isinstance(children, list):
        return 0
    return sum(1 + _count_below(c) for c in children if isinstance(c, dict))


def _number_sibling_clashes(siblings: list, new_steps: list[dict]) -> None:
    """Rename in place any new label that collides with existing
    siblings or with an earlier new peer (` (2)`, ` (3)`, …).

    Checks this level against existing siblings, then each new node's
    children among themselves (and so on).
    """
    seen: list = list(siblings)
    for step in new_steps:
        step["label"] = unique_sibling_label(seen, step.get("label") or "")
        seen.append(step)
        children = step.get("children")
        if isinstance(children, list) and children:
            _number_sibling_clashes([], children)


def _find_step(steps: list, step_id: str) -> tuple[dict, list[str]] | None:
    """The step with this id and its ancestors' labels (top first), or
    None. The tree walk itself is node.find_path()."""
    path = find_path(steps, step_id)
    if path is None:
        return None
    return path[-1], [step.get("label") or "" for step in path[:-1]]


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
