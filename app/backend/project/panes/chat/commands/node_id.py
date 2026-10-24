"""/id — show node identity behind the labels.

With a node selected: reply with that node's short id (its first
characters, backend/identity/) and label path.
Without one: tell the browser to switch the whole map between showing
ids and labels (a display toggle only; nothing about the tree changes,
and the tree is not dumped into the thread — docs/05-decisions.md #48).
No model.
"""

from backend.identity import short_id
from backend.project.node import find_path, nodes_of
from backend.project.panes.chat.commands.result import CommandResult

_TOGGLED = "Map switched between node ids and names. Type /id again to switch back."


def run(
    latest: dict,
    note: str,
    focus_node_id: str | None = None,
) -> CommandResult:
    del note  # /id takes no arguments
    if not focus_node_id:
        return CommandResult(_TOGGLED, toggle_map_ids=True)
    path = find_path(nodes_of(latest), focus_node_id)
    if path is None:
        return CommandResult(f"No node with id {focus_node_id}.")
    labels = " / ".join((part.get("label") or "").strip() for part in path)
    node = path[-1]
    return CommandResult(
        f"{node.get('label')} → {short_id(str(node.get('id')))} ({labels})"
    )
