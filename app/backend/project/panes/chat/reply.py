"""
You send a message, you get a reply back.

Cases:
- A slash-command (`/add`, `/select`, …): chat/commands/ runs it; same save
  path as an ordinary chat message (map-writing commands update the tree first).
- Anything else: the model answers, given what
  model/brief/conversation.py puts together.

The message and reply are saved, so the chat is still there after a
reload. The whole path and its rules: docs/chat.md.
"""

from backend.model.brief.budget import fit_to_budget
from backend.model.brief.conversation import build_messages
from backend.model.client import PROMPT_TOKENS, send_chat
from backend.project.node import find_node, nodes_of
from backend.project.panes.chat.commands import try_command
from backend.project.panes.create.resolver import get_history_for_project
from backend.project.status.build_status import (
    build_status,
    changes_text,
    status_text,
)
from backend.storage.paths import now_utc
from backend.storage.project_persistence import save_project


def reply(
    latest: dict,
    note: str,
    map_focus: str | None = None,
    focus_node_id: str | None = None,
    focus_day: str | None = None,
    about_removed: bool = False,
) -> dict:
    """{"record", "select"?, "toggle_map_ids"?} - the saved project
    record the screen is rebuilt from (its thread ends with the reply),
    and what a command asks the UI to do. `focus_day` (YYYY-MM-DD)
    is a selected day of changes; commands ignore it."""
    # Taken before the model is called: the reply can take a while, and
    # the message was sent now, not when the reply is saved.
    sent_at = now_utc()

    # The screen may still hold a node that was removed; a selection that
    # is not in the tree is no selection, unless the message was sent from
    # that removed node's own conversation (`about_removed`).
    gone = bool(focus_node_id and find_node(nodes_of(latest), focus_node_id) is None)
    if gone and not (about_removed and map_focus):
        map_focus = focus_node_id = None

    commanded = try_command(latest, note, focus_node_id=focus_node_id)
    if commanded is not None:
        text = commanded.reply
        # /select (or path /add with UI focus) frames About-focus.
        stamp_label = commanded.select_label or map_focus
        stamp_id = commanded.select_id or focus_node_id
        base = commanded.record if commanded.record is not None else latest
        record = save_chat_turn(
            base,
            note,
            text,
            sent_at,
            map_focus=stamp_label,
            focus_node_id=stamp_id,
        )
        out: dict = {"record": record}
        if commanded.select_id and commanded.select_label:
            out["select"] = {
                "id": commanded.select_id,
                "label": commanded.select_label,
            }
        if commanded.toggle_map_ids:
            out["toggle_map_ids"] = True
        return out

    history = get_history_for_project(latest["project_id"])
    status = "\n\n".join(
        filter(
            None,
            [
                status_text(build_status(history, current=latest)),
                changes_text(history),
            ],
        )
    )
    messages = build_messages(
        latest,
        note,
        history,
        map_focus,
        focus_node_id,
        status,
        focus_day=focus_day,
        about_removed=gone and about_removed,
    )
    text = send_chat(fit_to_budget(messages, PROMPT_TOKENS)).strip()
    record = save_chat_turn(
        latest,
        note,
        text,
        sent_at,
        map_focus=map_focus,
        focus_node_id=focus_node_id,
        focus_day=focus_day,
    )
    return {"record": record}


def save_chat_turn(
    latest: dict,
    note: str,
    text: str,
    sent_at: str,
    map_focus: str | None = None,
    focus_node_id: str | None = None,
    focus_day: str | None = None,
) -> dict:
    """Keep the map as it is; store the turn's message and reply in their
    own fields, which screen/chat_thread.py and model/brief/conversation.py
    read. The one way a chat turn is saved (also by backend/seed/)."""
    return save_project(
        latest.get("name") or "",
        nodes_of(latest),
        message=note,
        reply=text,
        project_id=latest["project_id"],
        account_id=latest.get("account_id"),
        event="chat",
        sent_at=sent_at,
        map_focus=map_focus,
        focus_node_id=focus_node_id,
        focus_day=focus_day,
    )
