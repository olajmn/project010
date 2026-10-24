"""
Puts together what the model is sent when you press Send, in order:

1. The system text: the fixed slots from talk_prompt.py, then the
   project background — its summary rows and last changes
   (project/status/; the panel above the chat shows the summary and a
   per-day count instead), every name in its structure, and the part
   or the day of changes you have selected.
2. The earlier chat, as real back-and-forth messages.
3. Your new message.

No model call, nothing saved.
"""

from backend.model.brief.talk_prompt import BEHAVIOR, EXAMPLES, LIMITS, ROLE, TASK
from backend.project.node import find_path, path_lines, steps_of, tree_lines
from backend.project.status.build_status import changes_on_day_text, day_name

# Earlier turns kept per Send. Bounds prompt size on a local model;
# older turns stay saved and shown, just not re-sent.
MAX_TURNS = 20


def build_messages(
    latest: dict,
    note: str,
    history: list[dict],
    map_focus: str | None = None,
    focus_step_id: str | None = None,
    status: str | None = None,
    focus_day: str | None = None,
) -> list[dict]:
    """[{role, content}] for model.client.send_chat(). `status` is the
    project's status text (status/build_status.status_text()).
    `focus_day` (YYYY-MM-DD) is a selected day of changes; that day's
    changes are read from `history`.

    Only `focus_step_id` decides the selected part, and only when the
    part is in the tree now; `map_focus` is the label the screen showed
    and is not read here."""
    steps = steps_of(latest)
    selected_day = changes_on_day_text(history, focus_day) if focus_day else None
    system = _system_text(latest, focus_step_id, status, selected_day)
    messages = [{"role": "system", "content": system}]
    messages.extend(past_turns(history, steps))
    # No saved label to fall back on: a selected part not in the tree is none.
    part = _part_name(None, focus_step_id, steps)
    messages.append(
        {"role": "user", "content": _with_focus(note, part or _day_tag(focus_day))}
    )
    return messages


def past_turns(
    history: list[dict],
    steps: list | None = None,
) -> list[dict]:
    """Saved chat turns as alternating user/assistant messages, oldest
    first. Map edits and the project's first record carry no chat turn
    and are skipped.

    With `steps` (the tree now), a turn's part is named by its path, as
    it is called today, with its name then after a rename, or marked as
    removed; without, by the label saved with the turn."""
    turns: list[dict] = []
    for record in history:
        if record.get("event") != "chat":
            continue
        note = record.get("message") or ""
        reply = record.get("reply") or ""
        then = record.get("map_focus")
        part = (
            then
            if steps is None
            else _part_name(then, record.get("focus_step_id"), steps)
        )
        focus = part or _day_tag(record.get("focus_day"))
        turns.append({"role": "user", "content": _with_focus(note, focus)})
        turns.append({"role": "assistant", "content": reply})
    return turns[-2 * MAX_TURNS :]


def _system_text(
    latest: dict,
    focus_step_id: str | None,
    status: str | None = None,
    selected_day: str | None = None,
) -> str:
    slots = [
        ("ROLE", ROLE),
        ("TASK", TASK),
        ("BEHAVIOR", BEHAVIOR),
        ("LIMITS", LIMITS),
        ("EXAMPLES", EXAMPLES),
        (
            "PROJECT BACKGROUND",
            _background(latest, focus_step_id, status, selected_day),
        ),
    ]
    return "\n\n".join(f"{title}\n{text}" for title, text in slots if text)


def _background(
    latest: dict,
    focus_step_id: str | None,
    status: str | None,
    selected_day: str | None = None,
) -> str:
    """The project as reference for this Send: name, status, map, and
    the selected node or day of changes."""
    name = (latest.get("name") or "").strip() or "untitled"
    parts = [
        "Reference for this conversation; look things up here when the "
        "question needs it.",
        f'Project: "{name}"',
    ]
    if status:
        # Computed from the project's saved changes, so it is fact; the
        # chat below is conversation.
        parts.append(
            "Status (computed from the project's saved changes; treat it "
            "as fact):\n" + status
        )
    steps = steps_of(latest)
    structure = "\n".join(tree_lines(steps)) or "The project has no parts yet."
    parts.append(
        "Structure (names only, each indented under the part it belongs "
        "to):\n" + structure
    )
    # Path from the top down to the selected part; nothing when the part
    # is not in the tree now.
    selected = "\n".join(path_lines(steps, focus_step_id)) if focus_step_id else ""
    if selected:
        parts.append(
            "The user has selected this part (shown with what it sits under "
            "and what it contains):\n" + selected
        )
    elif selected_day:
        parts.append(selected_day)
    else:
        parts.append(
            "Nothing is selected right now; talk about the project as a "
            "whole, not about a part from earlier in the conversation."
        )
    return "\n\n".join(parts)


_REMOVED = " (since removed)"


def _part_name(then: str | None, step_id: str | None, steps: list) -> str | None:
    """A part as the model is told about it: its path from the top
    ("Rooms / Planning"), with "(then called <then>)" after a rename, or
    "<then> (since removed)" when it is no longer in the tree. Without an
    id, the label saved with the turn."""
    then = (then or "").strip()
    wanted = (step_id or "").strip()
    if not wanted:
        return then or None
    path = find_path(steps, wanted)
    if path is None:
        return f"{then}{_REMOVED}" if then else None
    names = [(step.get("label") or "").strip() for step in path]
    name = " / ".join(names)
    if then and then != names[-1]:
        name += f" (then called {then})"
    return name


def _day_tag(focus_day: str | None) -> str | None:
    """A turn about one day of changes: "changes on 27 Sep"."""
    day = (focus_day or "").strip()
    return f"changes on {day_name(day)}" if day else None


def _with_focus(note: str, focus: str | None) -> str:
    """Tags a message with the node it was about, so turns about
    different nodes stay distinguishable in one conversation."""
    return f"[about: {focus}] {note}" if focus else note
