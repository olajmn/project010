"""
Project persistence: current.json (SoT for map/chat) + events.jsonl
(slim change tape for Current state/Logs) under data/projects/{id}/.

Identity grouping for display lives in create/resolver.py. A new
project's id comes from backend/identity/ and is also its folder name.
Accounts live in accounts_persistence.py and are only referenced via
optional account_id.
"""

# Contents
#  1. Identity
#      - PROJECTS_DIR / record_project_id()
#  2. Project records (current.json + events.jsonl)
#      - project_dir() / current_path() / events_path()
#      - _slim_event()
#      - load_current() / load_project_events() / save_project()
#      - load_all_currents() / delete_project()

import json
import shutil
from pathlib import Path

from backend.identity import new_project_id
from backend.storage import sandboxes
from backend.storage.jsonl import append_jsonl, read_jsonl
from backend.storage.paths import DATA_DIR, DEFAULT_USER_ID, now_utc

PROJECTS_DIR = DATA_DIR / "projects"


# ============================================================
# 1. Identity
# ============================================================


def record_project_id(record: dict) -> str | None:
    """A history record's project id, or None when it has none."""
    pid = record.get("project_id")
    return str(pid) if pid is not None else None


# ============================================================
# 2. Project records (data/projects/{id}/current.json + events.jsonl)
# ============================================================
#
# Current is the source of truth for map/chat. Events are a slim change
# tape for Current state/Logs. Each save updates current and appends one event
# (no full map on the tape).


def _projects_dir() -> Path:
    """PROJECTS_DIR, or projects/ in the visitor's demo sandbox."""
    sandbox = sandboxes.current()
    return sandbox / "projects" if sandbox else PROJECTS_DIR


def project_dir(project_id: str) -> Path:
    """data/projects/{id}/ — current + events for one project."""
    return _projects_dir() / project_id


def current_path(project_id: str) -> Path:
    return project_dir(project_id) / "current.json"


def events_path(project_id: str) -> Path:
    return project_dir(project_id) / "events.jsonl"


def _slim_event(record: dict) -> dict:
    """Drop the full map from a history line; keep tape fields."""
    event: dict = {
        "id": record.get("id"),
        "project_id": record_project_id(record),
        "user_id": record.get("user_id", DEFAULT_USER_ID),
        "created_at": record.get("created_at"),
    }
    for key in (
        "event",
        "feedback",
        "sent_at",
        "map_focus",
        "focus_node_id",
        "focus_day",
        "message",
        "reply",
        "name",
        "account_id",
        "cancelled",
        "archived_at",
    ):
        if key in record and record[key] is not None:
            event[key] = record[key]
    return event


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def _read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} is not a JSON object.")
    return data


def _iter_current_paths() -> list[tuple[str, Path]]:
    """(project_id, current.json path) for every on-disk project folder."""
    projects_dir = _projects_dir()
    if not projects_dir.exists():
        return []
    out: list[tuple[str, Path]] = []
    for path in projects_dir.iterdir():
        cur = path / "current.json"
        if path.is_dir() and cur.exists():
            out.append((path.name, cur))
    return out


def _existing_project_ids() -> list[str]:
    """Ids of the projects that have a current.json."""
    return [pid for pid, _ in _iter_current_paths()]


def load_current(project_id: str) -> dict | None:
    """The project's current SoT record, or None."""
    path = current_path(project_id)
    if not path.exists():
        return None
    return _read_json(path)


def load_project_events(project_id: str) -> list[dict]:
    """Slim change tape for one project, oldest first."""
    return read_jsonl(events_path(project_id))


def load_project_history(project_id: str) -> list[dict]:
    """Compatibility alias: the events tape (Current state/chat/timeline)."""
    return load_project_events(project_id)


def save_project(
    name: str,
    nodes: list[dict],
    feedback: str | None = None,
    cancelled: bool = False,
    project_id: str | None = None,
    account_id: str | None = None,
    event: str | None = None,
    sent_at: str | None = None,
    map_focus: str | None = None,
    focus_node_id: str | None = None,
    focus_day: str | None = None,
    message: str | None = None,
    reply: str | None = None,
    change: dict | None = None,
) -> dict:
    """
    Update the project's current SoT and append one slim event.

    Callers pass the full project fields; only current.json keeps the
    map (`nodes`, the top-level nodes with everything under them). The
    events tape stores event/feedback/times, not a copy of the map.

    `map_focus` / `focus_step_id` mark this chat turn as about a selected
    node (About frames + model history); `focus_step_id` alone marks a
    map edit on one node (a rename), for that node's chat. They are not
    inherited from the previous current — pass them only when this save
    is focused.
    `focus_day` (YYYY-MM-DD) marks a chat turn about one day's changes
    instead, the same way.
    `message` / `reply` are a chat turn's two sides, each in its own field.
    `change` is a map edit's full record (project/changes/records.py); it
    goes to the events line only, not to current.json.

    Returns the current record that was saved.
    """
    pid = project_id if project_id is not None else new_project_id()
    existing_events = load_project_events(pid)
    record = {
        "id": len(existing_events) + 1,
        "user_id": DEFAULT_USER_ID,
        "project_id": pid,
        "account_id": account_id,
        "name": name,
        "nodes": nodes,
        "feedback": feedback,
        "cancelled": cancelled,
        "created_at": now_utc(),
    }
    if event:
        record["event"] = event
    if sent_at:
        record["sent_at"] = sent_at
    focus = (map_focus or "").strip()
    if focus:
        record["map_focus"] = focus
    # Also on its own: a node rename names its node by id only.
    node = (focus_node_id or "").strip()
    if node:
        record["focus_node_id"] = node
    day = (focus_day or "").strip()
    if day:
        record["focus_day"] = day
    if message is not None:
        record["message"] = message
    if reply is not None:
        record["reply"] = reply

    _write_json(current_path(pid), record)
    line = _slim_event(record)
    if change is not None:
        line["change"] = change
    append_jsonl(events_path(pid), line)
    return record


def load_all_currents() -> list[dict]:
    """Current SoT record for every project."""
    currents: list[dict] = []
    for pid in sorted(_existing_project_ids()):
        current = load_current(pid)
        if current is not None:
            currents.append(current)
    return currents


def delete_project(project_id: str) -> bool:
    """Permanently remove data/projects/{id}/ (current + events).

    Returns True if a store was removed, False if none existed.
    """
    path = project_dir(project_id)
    if not path.exists():
        return False
    shutil.rmtree(path)
    return True
