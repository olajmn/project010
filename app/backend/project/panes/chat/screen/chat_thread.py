"""
The list of messages shown in the chat panel.

Built from saved chat - no model call. A line saved with
`event: "chat"` is one user line (its `message`) and one agent line
(its `reply`). One kind of map edit also shows, as a quiet note:
renaming a node that has been talked about, inside that node's
conversation, so earlier turns that use the old name still make sense
(docs/05-decisions.md #71). Other map edits, archive lines, and the
project's first record belong in Status, not here — same rule as
model/brief/conversation.past_turns().
"""

from backend.project.node import find_path
from backend.project.panes.create.resolver import get_history_for_project

# A node rename is saved as "Renamed step: <old> → <new>"
# (panes/canvas/edit_map.rename_map_node()).
_RENAME_PREFIX = "Renamed step: "
_RENAME_ARROW = " → "


def thread_messages(history: list[dict], steps: list | None = None) -> list[dict]:
    """[{role, text, focus?}] oldest first - each saved chat turn is one
    user line (the note) and one agent line (the reply).

    When a turn was map-focused (Talk about this / Looking at), both
    lines carry `focus: "<node label>"` (and `focus_step_id` when known)
    so the UI can frame that stretch, show where it ends, and re-select
    the node from the frame. A turn about a day of changes carries
    `focus_day` (YYYY-MM-DD) instead.

    Each message carries `at`, when it happened: the agent line the
    record's `created_at`, the user line `sent_at` when saved (chat turns
    since 2026-09-25), else `created_at`.

    A rename of a node that has chat turns becomes one `role: "note"`
    line with that node's `focus_step_id` and its new label as `focus`.

    With `steps` (the tree now), both lines of a turn about a node that
    is no longer in it carry `removed: True`, and a turn about a node
    whose label another node also has carries `focus_context`: the
    labels above it that tell the two apart ("Design"). A turn about a
    node in the tree carries `focus_path`, its labels from the top."""
    talked_about = {
        (r.get("focus_step_id") or "").strip()
        for r in history
        if r.get("event") == "chat"
    } - {""}
    contexts = _contexts(steps) if steps is not None else {}
    messages: list[dict] = []
    for record in history:
        note_line = _rename_note(record, talked_about)
        if note_line:
            messages.append(note_line)
            continue
        if record.get("event") != "chat":
            continue
        note = record.get("message") or ""
        reply = record.get("reply") or ""
        focus = (record.get("map_focus") or "").strip() or None
        step = (record.get("focus_step_id") or "").strip() or None
        extra: dict = {}
        day = (record.get("focus_day") or "").strip() or None
        if focus:
            extra["focus"] = focus
            if step:
                extra["focus_step_id"] = step
                path = find_path(steps, step) if steps is not None else None
                if steps is not None and path is None:
                    extra["removed"] = True
                elif path is not None:
                    extra["focus_path"] = " / ".join(
                        (node.get("label") or "").strip() for node in path
                    )
                    if step in contexts:
                        extra["focus_context"] = contexts[step]
        elif day:
            extra["focus_day"] = day
        created_at = record.get("created_at")
        messages.append(
            {
                "role": "user",
                "text": note,
                **_at(record.get("sent_at") or created_at),
                **extra,
            }
        )
        messages.append({"role": "agent", "text": reply, **_at(created_at), **extra})
    return messages


def thread_for(
    project_id: str,
    history: list[dict] | None = None,
    steps: list | None = None,
) -> list[dict]:
    """Live thread for one project. Pass `history` when the caller
    already loaded it, and `steps` (the tree now) for what
    thread_messages() adds from it: removed, path, and context."""
    if history is None:
        history = get_history_for_project(project_id)
    return thread_messages(history, steps)


def _contexts(steps: list) -> dict[str, str]:
    """{node id: the nearest labels above it that tell it apart} for each
    node whose label another node also has; the fewest levels that do."""
    found: list[tuple[str, str, list[str]]] = []

    def walk(nodes: list, above: list[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            label = (node.get("label") or "").strip()
            found.append((str(node.get("id") or ""), label, above))
            walk(node.get("children") or [], [*above, label])

    walk(steps, [])
    by_label: dict[str, list[tuple[str, list[str]]]] = {}
    for step_id, label, above in found:
        by_label.setdefault(label, []).append((step_id, above))
    contexts: dict[str, str] = {}
    for same in by_label.values():
        if len(same) < 2:
            continue
        for step_id, above in same:
            for levels in range(1, len(above) + 1):
                tail = above[-levels:]
                if sum(other[-levels:] == tail for _, other in same) == 1:
                    break
            contexts[step_id] = " / ".join(above[-levels:]) if above else ""
    return {k: v for k, v in contexts.items() if k and v}


def _rename_note(record: dict, talked_about: set[str]) -> dict | None:
    """The quiet "Renamed from … to …" line for a node rename, or None
    when the record is not one or the node was never talked about."""
    if record.get("event") != "node_renamed":
        return None
    step = (record.get("focus_step_id") or "").strip()
    feedback = record.get("feedback") or ""
    if step not in talked_about or not feedback.startswith(_RENAME_PREFIX):
        return None
    old, sep, new = feedback[len(_RENAME_PREFIX) :].partition(_RENAME_ARROW)
    if not sep:
        return None
    return {
        "role": "note",
        "text": f"Renamed from “{old}” to “{new}”",
        "focus": new,
        "focus_step_id": step,
        **_at(record.get("created_at")),
    }


def _at(when: str | None) -> dict:
    """{"at": when}, or nothing when the record has no time."""
    return {"at": when} if when else {}
