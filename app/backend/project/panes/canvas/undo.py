"""
Undo and redo on the map: the change to act on comes from the log
(project/changes/undo.py), the tree changes the way a replay would
(changes/replay.py), and the result is saved like any map edit, as a
new line with its own record. No model call.
"""

import copy

from backend.project.changes import records
from backend.project.changes.replay import apply_change
from backend.project.changes.undo import base_feedback, next_redo, next_undo
from backend.project.panes.canvas.edit_map import save_map_edit
from backend.storage.project_persistence import load_project_events


def undo_map_change(latest: dict, since: int) -> dict:
    """Reverse the latest change made after log line `since`. Raises
    ValueError when there is none."""
    line = next_undo(load_project_events(latest["project_id"]), since)
    if line is None:
        raise ValueError("nothing to undo")
    change = records.reversed_change(line["change"])
    return _save(latest, change, f"Undid: {base_feedback(line)}", "undone")


def redo_map_change(latest: dict, since: int) -> dict:
    """Do again the latest change undone after log line `since`. Raises
    ValueError when there is none."""
    line = next_redo(load_project_events(latest["project_id"]), since)
    if line is None:
        raise ValueError("nothing to redo")
    change = records.repeated_change(line["change"])
    return _save(latest, change, f"Redid: {base_feedback(line)}", "redone")


def _save(latest: dict, change: dict, feedback: str, event: str) -> dict:
    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        progression = {"steps": []}
        plan["progression"] = progression
    steps = progression.setdefault("steps", [])
    apply_change(steps, change)
    if not steps:
        plan["progression"] = None
    # A move or rename names its node, so that node's chat shows it.
    return save_map_edit(
        latest, plan, feedback, event, change, focus_step_id=change.get("node_id")
    )
