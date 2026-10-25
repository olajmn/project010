"""
A project's timeline: every saved change, in order, as plain events —
created, chat, node added, renamed, archived, ...

Every change is already saved as one timestamped line in
data/projects/{id}/events.jsonl (storage/project_persistence.py). This file only reads
those lines back as events; it writes nothing. Used by the project
timeline address (/api/projects/<id>/timeline), which a project's
Details page in Settings shows. See docs/04-current-state.md § 2.
"""

# Contents
#  1. What happened
#      - GROUPS
#      - event_name()
#
#  2. Reading timelines
#      - project_timeline()
#      - to_event()

from backend.project.panes.create.resolver import (
    get_history_for_project,
)
from backend.storage.project_persistence import (
    load_current,
    record_project_id,
)

# ============================================================
# 1. What happened
# ============================================================

# Each saved line's `event` (written since 2026-09-25) → the group shown
# as the entry's title in a project's log (Settings → Details).
GROUPS = {
    "created": "Created",
    "chat": "Chat",
    "chat_added_nodes": "Chat",
    "node_added": "Map",
    "node_removed": "Map",
    "node_moved": "Map",
    "node_renamed": "Map",
    "pasted": "Map",
    "folder_added": "Map",
    "tree_inserted": "Map",
    "undone": "Map",
    "redone": "Map",
    "suggested": "Map",
    "renamed": "Renamed",
    "owner_changed": "Owner",
    "archived": "Archived",
    "restored": "Restored",
}

_TEXT_MAX = 160


def event_name(record: dict) -> str:
    """What this saved line was. Every line carries `event`; lines saved
    before it existed were given one by the 2026-09-27 conversion (#59)."""
    return record.get("event") or "other"


# ============================================================
# 2. Reading timelines
# ============================================================


def project_timeline(project_id: str) -> list[dict]:
    """One project's events, oldest first — its whole history."""
    history = get_history_for_project(project_id)
    current = load_current(project_id)
    name = (current or {}).get("name", "") or (
        history[-1].get("name", "") if history else ""
    )
    return [to_event(r, name) for r in history]


def to_event(record: dict, project_name: str) -> dict:
    """{at, project_id, project, event, kind, text, focus?} for one saved
    line. `project` is the project's current name; `text` is what a person
    would want to read: the chat message, or what changed; `focus` is the
    map node a chat message was about, when there was one."""
    name = event_name(record)
    feedback = (record.get("feedback") or "").strip()
    if name == "chat":
        text = (record.get("message") or "").strip()
    elif name in ("created", "archived", "restored"):
        text = ""
    else:
        text = feedback
    if len(text) > _TEXT_MAX:
        text = text[:_TEXT_MAX] + "…"
    event = {
        "at": record.get("created_at"),
        "project_id": record_project_id(record),
        "project": project_name,
        "event": name,
        "kind": GROUPS.get(name, "Other"),
        "text": text,
    }
    focus = (record.get("map_focus") or "").strip()
    if focus:
        event["focus"] = focus
    return event
