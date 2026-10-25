"""
Shapes the data sent back to the browser: a project with its map tree
and chat, the project list, a simulated user. Only reads and reshapes;
no product rules.
"""

# Contents
#  1. Project, project list, account
#      - project_view()
#      - active_projects() / archived_projects()
#      - account_view()
#      - saved_tree_view()
#
#  2. Map tree
#      - map_tree()

from backend.project.changes.undo import undo_state
from backend.project.current_state.build_current_state import build_current_state
from backend.project.node import count_nodes, nodes_of
from backend.project.panes.chat.screen.chat_thread import thread_for
from backend.project.panes.create.resolver import (
    created_at_key,
    get_history_for_project,
    get_latest_for_all_projects,
)
from backend.storage.project_persistence import record_project_id

# ============================================================
# 1. Project, project list, user
# ============================================================


def project_view(
    record: dict,
    select: dict | None = None,
    toggle_map_ids: bool = False,
) -> dict:
    """One project as the browser gets it after any project action:
    name, state, map tree, chat, and current state (the panel above the chat).

    A chat reply just made is already the last message in `thread`
    (it is saved before the view is built). `select` (optional
    `{id, label}` from `/select`) tells the UI to focus that node.
    `toggle_map_ids` (from `/id` with no node selected) tells the UI to
    switch the map between ids and labels.
    """
    pid = record_project_id(record)
    try:
        node = map_tree(record)
    except Exception as e:
        # A broken tree must not hide the rest of the project.
        print(f"(debug: map_tree() failed for project {pid}: {e})")
        node = None
    history = get_history_for_project(pid) if pid is not None else []
    thread = thread_for(pid, history, nodes_of(record)) if pid is not None else []
    view = {
        "project_id": pid,
        "name": record["name"],
        "cancelled": bool(record.get("cancelled")),
        "account_id": record.get("account_id"),
        "created_at": record.get("created_at"),
        # When it was made: its first log line (created_at is its latest).
        "started_at": history[0].get("created_at")
        if history
        else record.get("created_at"),
        # Where undo and redo would act; the page compares with where it opened.
        "undo": undo_state(history),
        "node": node,
        "thread": thread,
        "current_state": build_current_state(history, current=record),
    }
    if select and select.get("id") and select.get("label"):
        view["select"] = {
            "id": str(select["id"]),
            "label": str(select["label"]),
        }
    if toggle_map_ids:
        view["toggle_map_ids"] = True
    return view


def active_projects() -> list[dict]:
    """Every project that isn't cancelled, newest first."""
    latest = get_latest_for_all_projects()
    active = [r for r in latest if not r.get("cancelled")]
    active.sort(key=created_at_key, reverse=True)
    return active


def archived_projects() -> list[dict]:
    """Cancelled projects, newest first (Settings → Archive)."""
    latest = get_latest_for_all_projects()
    closed = [r for r in latest if r.get("cancelled")]
    closed.sort(key=created_at_key, reverse=True)
    return closed


def account_view(account: dict) -> dict:
    """{id, text, archived, created_at, archived_at?}. `archived` is only
    stored once true, so it is filled in here."""
    view = {
        "id": account["id"],
        "text": account["text"],
        "archived": bool(account.get("archived")),
        "created_at": account["created_at"],
    }
    if account.get("archived_at"):
        view["archived_at"] = account["archived_at"]
    return view


def saved_tree_view(saved: dict) -> dict:
    """{id, name, saved_at, node_count} — what the picker lists; the
    structure itself stays on the server until it is inserted."""
    tree = saved.get("tree")
    return {
        "id": saved["id"],
        "name": saved["name"],
        "saved_at": saved["saved_at"],
        "node_count": count_nodes([tree] if tree else []),
    }


# ============================================================
# 2. Map tree
# ============================================================


def map_tree(record: dict) -> dict | None:
    """The map as the browser draws it: {id, label, status, children},
    with the project as the root. None when the map is empty."""
    children = [_node(node) for node in nodes_of(record) if isinstance(node, dict)]
    if not children:
        return None
    return {
        "id": record["project_id"],
        "label": record.get("name", ""),
        "status": "open",
        "children": children,
    }


def _node(node: dict) -> dict:
    """One node and everything under it."""
    return {
        "id": str(node["id"]),
        "label": node.get("label") or "—",
        # Nothing writes `resolved` today, so every node shows "open".
        "status": "done" if node.get("resolved") else "open",
        "children": [
            _node(child)
            for child in node.get("children") or []
            if isinstance(child, dict)
        ],
    }
