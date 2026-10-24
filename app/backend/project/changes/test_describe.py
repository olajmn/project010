"""Checks for change lines the chat's model reads: names and paths at
the time of each change, never ids, and long lists cut with a note."""

from backend.project.changes import records
from backend.project.changes.describe import MAX_NAMES, describe_changes


def _node(node_id: str, label: str, children: list | None = None) -> dict:
    return {"id": node_id, "label": label, "children": children or []}


def _lines(*changes: tuple[str, dict]) -> dict[int, str]:
    history = [
        {"id": n, "event": event, "change": change}
        for n, (event, change) in enumerate(changes, start=1)
    ]
    return describe_changes(history)


def test_each_kind_names_its_nodes_and_where() -> None:
    kitchen = _node("node_k", "Kitchen")
    rooms = _node("node_r", "Rooms", [kitchen])
    garden = _node("node_g", "Garden")
    rename = records.renamed("node_k", "Kitchen", "Bath")
    lines = _lines(
        ("pasted", records.added(None, 0, [rooms, garden])),
        ("node_moved", records.moved("node_g", None, 1, 0)),
        ("node_renamed", rename),
        ("node_removed", records.removed("node_r", 0, [_node("node_k", "Bath")])),
        (
            "undone",
            records.reversed_change(
                records.removed("node_r", 0, [_node("node_k", "Bath")])
            ),
        ),
    )
    assert lines == {
        1: "Imported 3 nodes at the top level: Rooms (Kitchen), Garden",
        2: "Moved Garden above Rooms at the top level",
        3: "Renamed Kitchen to Bath under Rooms",
        4: "Removed Bath under Rooms",
        5: "Undo: Added Bath under Rooms",
    }
    assert not any("node_" in text for text in lines.values())


def test_a_long_list_is_cut_with_a_note() -> None:
    many = [_node(f"node_{n}", f"N{n}") for n in range(MAX_NAMES + 5)]
    text = _lines(("pasted", records.added(None, 0, many)))[1]
    assert text.endswith("… and 5 more")
    assert "N0" in text and f"N{MAX_NAMES}" not in text
