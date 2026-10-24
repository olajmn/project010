"""Checks for replay: change records rebuild the tree, and a record
that does not fit the tree is refused."""

import pytest

from backend.project.changes import records
from backend.project.changes.replay import replay


def _node(node_id: str, label: str, children: list | None = None) -> dict:
    return {"id": node_id, "label": label, "children": children or []}


def _line(change: dict) -> dict:
    return {"event": "pasted", "change": change}


def test_every_kind_of_change_replays() -> None:
    a, b = _node("node_a", "A"), _node("node_b", "B", [_node("node_c", "C")])
    events = [
        {"event": "created"},
        _line(records.added(None, 0, [a, b])),
        _line(records.moved("node_b", None, 1, 0)),
        _line(records.renamed("node_c", "C", "See")),
        _line(records.removed(None, 1, [a])),
        {"event": "chat", "message": "Hi"},
    ]
    assert replay(events) == [_node("node_b", "B", [_node("node_c", "See")])]


def test_a_map_edit_without_a_record_cannot_replay() -> None:
    with pytest.raises(ValueError, match="without a record"):
        replay([{"id": 2, "event": "pasted"}])


def test_a_record_that_does_not_fit_is_refused() -> None:
    events = [
        _line(records.added(None, 0, [_node("node_a", "A")])),
        _line(records.renamed("node_a", "Not A", "B")),
    ]
    with pytest.raises(ValueError, match="is not named"):
        replay(events)
