"""Checks for undo and redo as read from the log: which change is next,
where a visit's reach ends, and that the log still replays."""

from backend.project.changes import records
from backend.project.changes.replay import replay
from backend.project.changes.undo import next_redo, next_undo, undo_state


def _node(node_id: str, label: str) -> dict:
    return {"id": node_id, "label": label, "children": []}


class Log(list):
    """Log lines numbered 1, 2, … as save_project numbers them."""

    def save(self, change: dict) -> dict:
        line = {"id": len(self) + 1, "event": "pasted", "change": change}
        self.append(line)
        return line


def test_undo_goes_back_and_redo_forward() -> None:
    log = Log()
    a = log.save(records.added(None, 0, [_node("node_a", "A")]))["change"]
    b = log.save(records.added(None, 1, [_node("node_b", "B")]))["change"]

    assert next_undo(log, 0)["change"] is b
    log.save(records.reversed_change(b))
    assert next_undo(log, 0)["change"] is a
    log.save(records.reversed_change(a))
    assert next_undo(log, 0) is None and replay(log) == []

    assert next_redo(log, 0)["change"] is a
    log.save(records.repeated_change(a))
    assert next_redo(log, 0)["change"] is b
    log.save(records.repeated_change(b))
    assert next_redo(log, 0) is None
    assert replay(log) == [_node("node_a", "A"), _node("node_b", "B")]


def test_reach_ends_where_the_page_opened() -> None:
    log = Log()
    log.save(records.added(None, 0, [_node("node_a", "A")]))
    opened_at = undo_state(log)["log_lines"]
    assert next_undo(log, opened_at) is None
    change = log.save(records.renamed("node_a", "A", "Z"))["change"]
    assert next_undo(log, opened_at)["change"] is change


def test_a_removed_node_comes_back_in_its_place() -> None:
    log = Log()
    nodes = [_node("node_a", "A"), _node("node_b", "B"), _node("node_c", "C")]
    log.save(records.added(None, 0, nodes))
    removed = log.save(records.removed(None, 1, [nodes[1]]))["change"]
    log.save(records.reversed_change(removed))
    assert replay(log) == nodes


def test_a_new_change_ends_redo() -> None:
    log = Log()
    a = log.save(records.added(None, 0, [_node("node_a", "A")]))["change"]
    log.save(records.reversed_change(a))
    assert undo_state(log)["redo_line"] == 2
    log.save(records.added(None, 0, [_node("node_b", "B")]))
    assert next_redo(log, 0) is None and undo_state(log)["redo_line"] is None
