"""The saved text of remove_map_node(), import_map_outline(),
move_map_node() and rename_map_node() - no files, no model.
"""

import pytest

import backend.project.panes.canvas.edit_map as edit_map


@pytest.fixture
def saved(monkeypatch) -> dict:
    """What would be saved, captured instead of written to data/."""
    captured: dict = {}
    monkeypatch.setattr(
        edit_map,
        "save_plan",
        lambda name, plan, **kw: captured.update(kw, plan=plan) or kw,
    )
    return captured


def tree() -> dict:
    return {
        "name": "T",
        "project_id": 1,
        "plan": {
            "progression": {
                "steps": [
                    {
                        "id": "p1",
                        "label": "Top",
                        "children": [
                            {
                                "id": "p2",
                                "label": "Mid",
                                "children": [
                                    {"id": "p3", "label": "Leaf", "children": []},
                                ],
                            },
                        ],
                    },
                ]
            }
        },
    }


def row() -> dict:
    return {
        "name": "T",
        "project_id": 1,
        "plan": {
            "progression": {
                "steps": [
                    {"id": "p1", "label": "A", "children": []},
                    {
                        "id": "p2",
                        "label": "B",
                        "children": [
                            {"id": "p3", "label": "B1", "children": []},
                            {"id": "p4", "label": "B2", "children": []},
                        ],
                    },
                ]
            }
        },
    }


def order(steps: list) -> list[str]:
    return [s["id"] for s in steps]


def test_remove_says_where_and_what_went_with_it(saved) -> None:
    # So Logs and the chat's model need not guess.
    edit_map.remove_map_node(tree(), "p2")
    assert saved["feedback"] == "Removed step under Top: Mid (and 1 under it)", saved
    edit_map.remove_map_node(tree(), "p3")
    assert saved["feedback"] == "Removed step under Mid: Leaf"
    edit_map.remove_map_node(tree(), "p1")
    assert saved["feedback"] == "Removed step: Top (and 2 under it)"
    assert saved["event"] == "node_removed"


def test_import_counts_every_node(saved) -> None:
    # One import is one change, but its text counts every node it
    # brought in, not only the top level.
    forest = [
        {
            "label": "A",
            "children": [
                {"label": "B", "children": [{"label": "C", "children": []}]},
                {"label": "D", "children": []},
            ],
        }
    ]
    edit_map.import_map_outline(tree(), forest=forest)
    assert saved["feedback"] == "Imported 4 nodes", saved
    edit_map.import_map_outline(
        tree(), forest=[{"label": "E", "children": []}], parent_id="p3"
    )
    assert saved["feedback"] == "Imported 1 node under Leaf", saved


def test_move_swaps_with_one_sibling(saved) -> None:
    # Id and children go with it.
    edit_map.move_map_node(row(), "p2", "up")
    steps = saved["plan"]["progression"]["steps"]
    assert order(steps) == ["p2", "p1"], steps
    assert order(steps[0]["children"]) == ["p3", "p4"]
    assert saved["feedback"] == "Moved step: B above A", saved
    assert saved["event"] == "node_moved"
    edit_map.move_map_node(row(), "p3", "down")
    assert order(saved["plan"]["progression"]["steps"][1]["children"]) == ["p4", "p3"]
    assert saved["feedback"] == "Moved step under B: B1 below B2", saved


@pytest.mark.parametrize(
    "step_id, direction", [("p1", "up"), ("p4", "down"), ("p9", "up")]
)
def test_move_past_the_edge_or_unknown_fails(saved, step_id, direction) -> None:
    with pytest.raises(ValueError):
        edit_map.move_map_node(row(), step_id, direction)


def test_rename_keeps_id_place_and_children(saved) -> None:
    # The saved line carries the id so the chat can show the rename in
    # that node's conversation.
    edit_map.rename_map_node(row(), "p3", "  First  ")
    renamed = saved["plan"]["progression"]["steps"][1]
    assert renamed["children"][0] == {"id": "p3", "label": "First", "children": []}
    assert saved["feedback"] == "Renamed step: B1 → First", saved
    assert saved["event"] == "node_renamed"
    assert saved["focus_step_id"] == "p3"


def test_rename_to_same_name_saves_nothing(saved) -> None:
    same = row()
    assert edit_map.rename_map_node(same, "p3", "B1") is same and not saved


@pytest.mark.parametrize("step_id, label", [("p3", " "), ("p3", "B2"), ("p9", "X")])
def test_rename_refused(saved, step_id, label) -> None:
    # Empty, a sibling's name, or an unknown id.
    with pytest.raises(ValueError):
        edit_map.rename_map_node(row(), step_id, label)


def test_new_nodes_get_random_ids_and_no_counter(saved) -> None:
    import uuid

    edit_map.add_map_node(tree(), "Roof")
    added = saved["plan"]["progression"]["steps"][-1]
    assert uuid.UUID(added["id"].removeprefix("node_")).version == 4
    assert "node_id_hi" not in saved["plan"]
    forest = [{"label": "A", "children": [{"label": "B", "children": []}]}]
    edit_map.import_map_outline(tree(), forest=forest)
    top = saved["plan"]["progression"]["steps"][-1]
    assert uuid.UUID(top["id"].removeprefix("node_")).version == 4
    assert uuid.UUID(top["children"][0]["id"].removeprefix("node_")).version == 4


# Change records: what each edit did, saved with it (project/changes/).


def _record(saved: dict) -> dict:
    """The saved change record without its own id, after checking it."""
    from backend.identity import kind_of

    record = dict(saved["change"])
    assert kind_of(record.pop("id")) == "change"
    return record


def test_add_records_the_node_and_its_place(saved) -> None:
    edit_map.add_map_node(tree(), "Roof", parent_id="p1")
    change = _record(saved)
    added = saved["plan"]["progression"]["steps"][0]["children"][-1]
    assert change == {"op": "add", "parent": "p1", "index": 1, "nodes": [added]}


def test_import_records_every_node_brought_in(saved) -> None:
    forest = [{"label": "A", "children": [{"label": "B", "children": []}]}]
    edit_map.import_map_outline(tree(), forest=forest)
    change = _record(saved)
    top = saved["plan"]["progression"]["steps"][-1]
    assert change == {"op": "add", "parent": None, "index": 1, "nodes": [top]}
    assert change["nodes"][0]["children"][0]["label"] == "B"


def test_remove_records_the_whole_branch(saved) -> None:
    edit_map.remove_map_node(tree(), "p2")
    assert _record(saved) == {
        "op": "remove",
        "parent": "p1",
        "index": 0,
        "node": {
            "id": "p2",
            "label": "Mid",
            "children": [{"id": "p3", "label": "Leaf", "children": []}],
        },
    }


def test_move_and_rename_record_ids_and_values(saved) -> None:
    edit_map.move_map_node(row(), "p2", "up")
    assert _record(saved) == {
        "op": "move",
        "node_id": "p2",
        "parent": None,
        "from": 1,
        "to": 0,
    }
    edit_map.rename_map_node(row(), "p3", "First")
    assert _record(saved) == {
        "op": "rename",
        "node_id": "p3",
        "from": "B1",
        "to": "First",
    }


def test_a_record_does_not_change_with_the_tree(saved) -> None:
    edit_map.add_map_node(tree(), "Roof")
    saved["plan"]["progression"]["steps"][-1]["label"] = "Changed later"
    assert saved["change"]["nodes"][0]["label"] == "Roof"
