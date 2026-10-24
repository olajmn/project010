"""
Each change record as a line the chat's model can read: what happened,
by node names and their path in the tree at that moment, never ids
(TODO.md 54). The log is replayed as it goes, so a path is where the
node was when the change was made. A long list of names is cut with a
note. Logs keeps its own short sentences (timeline.py).
"""

from backend.project.changes.replay import apply_change
from backend.project.node import find_path

# Names listed for one change before the rest is counted instead.
MAX_NAMES = 40

_VERB = {
    "node_added": "Added",
    "pasted": "Imported",
    "tree_inserted": "Inserted",
    "folder_added": "Added from a folder",
}


def describe_changes(history: list[dict]) -> dict[int, str]:
    """{log line id: readable line} for every line with a change record.
    Stops describing at a record that does not fit the replayed tree
    (older lines keep their own sentence)."""
    steps: list[dict] = []
    out: dict[int, str] = {}
    for line in history:
        change = line.get("change")
        if change is None:
            continue
        try:
            text = _describe(steps, change, line.get("event"))
            apply_change(steps, change)
        except ValueError, KeyError:
            break
        out[line["id"]] = text
    return out


def _describe(steps: list[dict], change: dict, event: str | None) -> str:
    """One change, read against the tree just before it."""
    op = change["op"]
    where = _place(steps, change.get("parent"))
    if op == "add":
        nodes = change["nodes"]
        count = sum(_count(n) for n in nodes)
        verb = _VERB.get(event or "", "Added")
        if count == 1:
            text = f"{verb} {_names(nodes)} {where}"
        else:
            text = f"{verb} {count} nodes {where}: {_names(nodes)}"
    elif op == "remove":
        text = f"Removed {_names(change['nodes'])} {where}"
    elif op == "move":
        siblings = _siblings(steps, change.get("parent"))
        node = siblings[change["from"]]["label"]
        other = siblings[change["to"]]["label"]
        side = "above" if change["to"] < change["from"] else "below"
        text = f"Moved {node} {side} {other} {where}"
    else:
        path = find_path(steps, change["node_id"]) or []
        where = _place(steps, path[-2]["id"]) if len(path) > 1 else "at the top level"
        text = f"Renamed {change['from']} to {change['to']} {where}"
    if change.get("undoes"):
        return f"Undo: {text}"
    if change.get("redoes"):
        return f"Redo: {text}"
    return text


def _place(steps: list[dict], parent_id: str | None) -> str:
    """'under A > B' for a parent, or 'at the top level'."""
    if parent_id is None:
        return "at the top level"
    path = find_path(steps, parent_id) or []
    return "under " + " > ".join(str(s.get("label") or "") for s in path)


def _siblings(steps: list[dict], parent_id: str | None) -> list[dict]:
    if parent_id is None:
        return steps
    path = find_path(steps, parent_id) or [{}]
    return path[-1].get("children") or []


def _count(node: dict) -> int:
    return 1 + sum(_count(c) for c in node.get("children") or [])


def _names(nodes: list[dict]) -> str:
    """'A (B, C (D)), E' — every node with what is under it, cut after
    MAX_NAMES names with a note of how many more."""
    shown = 0
    total = sum(_count(n) for n in nodes)

    def walk(items: list[dict]) -> str:
        nonlocal shown
        parts = []
        for node in items:
            if shown >= MAX_NAMES:
                break
            shown += 1
            text = str(node.get("label") or "")
            children = node.get("children") or []
            if children and shown < MAX_NAMES:
                text += f" ({walk(children)})"
            parts.append(text)
        return ", ".join(parts)

    text = walk(nodes)
    if shown < total:
        text += f" … and {total - shown} more"
    return text
