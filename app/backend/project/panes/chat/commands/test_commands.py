"""Checks for slash-command dispatch — no model call."""

import backend.project.panes.canvas.edit_map as edit_map
from backend.project.panes.chat.commands import add as add_mod
from backend.project.panes.chat.commands import try_command

EMPTY = {
    "name": "Empty",
    "project_id": 1,
    "plan": {"progression": {"steps": []}},
}

TREE = {
    "name": "T",
    "project_id": 99,
    "plan": {
        "progression": {
            "steps": [
                {
                    "id": "p1",
                    "label": "CLIENT",
                    "children": [
                        {
                            "id": "p2",
                            "label": "hey3",
                            "children": [],
                        },
                    ],
                }
            ]
        }
    },
}


def test_plain_text_is_not_a_command() -> None:
    assert try_command(EMPTY, "hello") is None
    assert try_command(EMPTY, "") is None


def test_unknown_command_answers_without_the_model() -> None:
    unknown = try_command(EMPTY, "/id¨")
    assert unknown is not None and unknown.record is None
    assert unknown.reply.startswith("Unknown command /id¨.")
    assert not unknown.toggle_map_ids


def test_add_without_place_saves_nothing() -> None:
    # Missing focus / parent.
    result = try_command(EMPTY, "/add")
    assert result is not None and result.record is None
    assert "Usage" in result.reply

    result = try_command(EMPTY, "/add alone")
    assert result is not None and result.record is None
    assert "Usage" in result.reply

    result = try_command(EMPTY, "/add Missing / Child")
    assert result is not None and result.record is None
    assert "No node at path" in result.reply


def test_add_resolves_parent_and_child() -> None:
    parent_id, child, err = add_mod._resolve(TREE, "client", "p1")
    assert err is None and parent_id == "p1" and child == "client"
    parent_id, child, err = add_mod._resolve(TREE, "CLIENT / bills", None)
    assert err is None and parent_id == "p1" and child == "bills"
    parent_id, child, err = add_mod._resolve(TREE, "CLIENT / hey3 / hey", None)
    assert err is None and parent_id == "p2" and child == "hey"
    parent_id, child, err = add_mod._resolve(TREE, "CLIENT / missing / hey", None)
    assert parent_id is None and "No node at path" in (err or "")


def test_malformed_path_is_refused() -> None:
    # Must not mint a label that contains "/".
    bad = try_command(TREE, "/add CLIENT /hey")
    assert bad is not None and bad.record is None
    assert "spaces around" in bad.reply.lower()
    bad = try_command(TREE, "/add client /add hey /hey")
    assert bad is not None and bad.record is None
    assert "spaces around" in bad.reply.lower()
    bad = try_command(TREE, "/select CLIENT /hey")
    assert bad is not None and bad.select_id is None
    assert "spaces around" in bad.reply.lower()


def test_select_by_path() -> None:
    selected = try_command(TREE, "/select CLIENT / hey3")
    assert selected is not None
    assert selected.select_id == "p2"
    assert selected.select_label == "hey3"
    assert "Selected:" in selected.reply
    assert try_command(TREE, "/focus CLIENT").select_id == "p1"


def test_id_shows_selected_node_or_toggles_map() -> None:
    shown = try_command(TREE, "/id", focus_step_id="p2")
    assert shown.reply == "hey3 → p2 (CLIENT / hey3)", shown.reply
    assert not shown.toggle_map_ids and shown.record is None
    toggled = try_command(TREE, "/id")
    assert toggled.toggle_map_ids and toggled.record is None


def test_clashing_sibling_label_is_numbered(monkeypatch) -> None:
    # Numbered, not refused (decision #53).
    monkeypatch.setattr(
        edit_map,
        "save_plan",
        lambda name, plan, **kw: {"name": name, "plan": plan, **kw},
    )
    dup = try_command(TREE, "/add CLIENT / hey3")
    assert dup is not None and dup.record is not None
    assert dup.reply.endswith(": hey3 (2)."), dup.reply
