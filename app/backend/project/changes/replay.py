"""
Replay: the tree rebuilt from empty by applying a project's change
records (records.py) in log order, and the check that this gives
exactly the tree in current.json. The log is the account of what
happened; current.json is its quick answer (TODO.md 54).

Run from app/ to check every project under a data folder:
    python -m backend.project.changes.replay data
"""

import copy
import json
import sys
from pathlib import Path

from backend.project.node import find_path, nodes_of

# Log lines that change the map; each carries a `change` record.
MAP_EDITS = {
    "node_added",
    "node_removed",
    "node_moved",
    "node_renamed",
    "pasted",
    "folder_added",
    "tree_inserted",
    "undone",
    "redone",
}


def replay(events: list[dict]) -> list[dict]:
    """The top-level nodes after every change in `events`, oldest first.
    Raises ValueError on a map edit without a record, or a record that
    does not fit the tree it is applied to."""
    tree: list[dict] = []
    for line in events:
        change = line.get("change")
        if change is None:
            if line.get("event") in MAP_EDITS:
                raise ValueError(f"line {line.get('id')}: map edit without a record")
            continue
        apply_change(tree, change)
    return tree


def mismatch(project_dir: Path) -> str | None:
    """Why replaying this project's log does not give its current.json,
    or None when it does."""
    current = json.loads((project_dir / "current.json").read_text(encoding="utf-8"))
    events_file = project_dir / "events.jsonl"
    lines = (
        events_file.read_text(encoding="utf-8").splitlines()
        if events_file.exists()
        else []
    )
    try:
        rebuilt = replay([json.loads(line) for line in lines if line.strip()])
    except ValueError as err:
        return str(err)
    saved = nodes_of(current)
    return None if rebuilt == saved else "replayed tree differs from current.json"


def apply_change(tree: list[dict], change: dict) -> None:
    """Apply one record to `tree` (the top-level nodes) in place, as the
    edit did. Raises ValueError if the record does not fit the tree."""
    op = change.get("op")
    if op in ("add", "remove"):
        siblings = children_of(tree, change["parent"])
        index, nodes = change["index"], change["nodes"]
        if op == "add":
            if not 0 <= index <= len(siblings):
                raise ValueError(f"{change['id']}: no place {index} to add at")
            siblings[index:index] = copy.deepcopy(nodes)
            return
        if [s.get("id") for s in siblings[index : index + len(nodes)]] != [
            n["id"] for n in nodes
        ]:
            raise ValueError(
                f"{change['id']}: the nodes are not where they were removed"
            )
        del siblings[index : index + len(nodes)]
    elif op == "move":
        siblings = children_of(tree, change["parent"])
        i, j = change["from"], change["to"]
        if not _at(siblings, i, change["node_id"]) or not 0 <= j < len(siblings):
            raise ValueError(
                f"{change['id']}: {change['node_id']} cannot move {i} to {j}"
            )
        siblings[i], siblings[j] = siblings[j], siblings[i]
    elif op == "rename":
        path = find_path(tree, change["node_id"])
        if path is None or path[-1].get("label") != change["from"]:
            raise ValueError(
                f"{change['id']}: {change['node_id']} is not named {change['from']}"
            )
        path[-1]["label"] = change["to"]
    else:
        raise ValueError(f"{change.get('id')}: unknown op {op}")


def children_of(tree: list[dict], parent_id: str | None) -> list[dict]:
    """The sibling list under `parent_id` (the top level for None); a
    node without children gets an empty list to add to."""
    if parent_id is None:
        return tree
    path = find_path(tree, parent_id)
    if path is None:
        raise ValueError(f"parent not found: {parent_id}")
    return path[-1].setdefault("children", [])


def _at(siblings: list[dict], index: int, node_id: str) -> bool:
    return 0 <= index < len(siblings) and siblings[index].get("id") == node_id


def main(data_root: Path) -> int:
    """Print every project whose log does not replay to its current.json;
    1 if any, 0 if none."""
    problems = 0
    for project_dir in sorted((data_root / "projects").iterdir()):
        if not (project_dir / "current.json").exists():
            continue
        why = mismatch(project_dir)
        if why:
            problems += 1
            print(f"  {project_dir.name}: {why}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "data")))
