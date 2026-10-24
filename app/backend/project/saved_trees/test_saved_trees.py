"""Checks for saved trees — no model call, no writes to data/."""

import pytest

import backend.project.panes.canvas.edit_map as edit_map
import backend.storage.saved_trees_persistence as store
from backend.project.saved_trees import (
    insert_saved_tree,
    remove_saved_tree,
    save_tree_from_node,
    saved_trees_for,
)


def _project(project_id: str, account: str | None, nodes: list) -> dict:
    return {
        "name": "P",
        "project_id": project_id,
        "account_id": account,
        "nodes": nodes,
    }


RECIPE = {
    "id": "node_1",
    "label": "Pasta Bolognese",
    "resolved": True,
    "ordered": False,
    "children": [
        {
            "id": "node_2",
            "label": "Ingredients",
            "path": "/tmp/x",
            "children": [
                {"id": "node_3", "label": "Pasta", "children": []},
            ],
        },
        {"id": "node_4", "label": "Method", "children": []},
    ],
}
SOURCE = _project("project_1", "account_7", [RECIPE])


@pytest.fixture(autouse=True)
def library(tmp_path, monkeypatch):
    """An empty saved-tree file per test; project saves return the record
    instead of writing it."""
    monkeypatch.setattr(store, "SAVED_TREES_FILE", tmp_path / "saved_trees.json")
    monkeypatch.setattr(
        edit_map,
        "save_project",
        lambda name, nodes, **kw: {"name": name, "nodes": nodes, **kw},
    )


@pytest.fixture
def saved() -> dict:
    return save_tree_from_node(SOURCE, "node_1")


def test_saved_as_structure(saved) -> None:
    # No id, resolved, or path anywhere.
    assert saved["id"] == "t1" and saved["name"] == "Pasta Bolognese"
    assert saved["source"] == {"project_id": "project_1", "node_id": "node_1"}
    tree = saved["tree"]
    assert tree["ordered"] is False
    flat = repr(tree)
    assert "'id'" not in flat and "resolved" not in flat and "path" not in flat


def test_library_is_per_account(saved) -> None:
    assert [t["id"] for t in saved_trees_for(SOURCE)] == ["t1"]
    assert saved_trees_for(_project("project_2", "account_8", [])) == []


def test_insert_under_a_node(saved) -> None:
    # Under a node that already has the same label: fresh ids, numbered
    # top label, `ordered` kept.
    target = _project(
        "project_3",
        "account_7",
        [
            {
                "id": "node_5",
                "label": "Recipes",
                "children": [
                    {"id": "node_6", "label": "Pasta Bolognese", "children": []},
                ],
            }
        ],
    )
    record = insert_saved_tree(target, "t1", "node_5")
    recipes = record["nodes"][0]["children"]
    inserted = recipes[-1]
    assert inserted["label"] == "Pasta Bolognese (2)"
    assert inserted["ordered"] is False and inserted["resolved"] is False
    ids = [inserted["id"], *(c["id"] for c in inserted["children"])]
    assert "node_1" not in ids and "node_2" not in ids and len(set(ids)) == len(ids)
    assert [c["label"] for c in inserted["children"]] == ["Ingredients", "Method"]


def test_insert_at_top_level(saved) -> None:
    top = insert_saved_tree(_project("project_3", "account_7", []), "t1", None)
    assert top["nodes"][-1]["label"] == "Pasta Bolognese"


def test_other_accounts_tree_cannot_be_inserted(saved) -> None:
    with pytest.raises(ValueError):
        insert_saved_tree(_project("project_4", "account_8", []), "t1", None)


def test_delete_retires_the_id(saved) -> None:
    remove_saved_tree("t1")
    assert saved_trees_for(SOURCE) == []
    assert save_tree_from_node(SOURCE, "node_1")["id"] == "t2"
