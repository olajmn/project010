"""Checks for build_messages() / past_turns() - no model call."""

from backend.model.brief.conversation import (
    MAX_TURNS,
    build_messages,
    past_turns,
)

LATEST = {
    "name": "Garden",
    "plan": {"progression": {"steps": [
        {"id": "p1", "label": "Beds", "children": []},
    ]}},
}
HISTORY = [
    {"feedback": None},  # first record: no turn
    {"feedback": "Zoomed into: Beds"},  # map edit: no turn
    {"feedback": "Sounds good. Note: hello"},
    {"feedback": "Beds hold soil. Note: what is this", "map_focus": "Beds"},
]
TURNS = [
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": "Sounds good."},
    {"role": "user", "content": "[about: Beds] what is this"},
    {"role": "assistant", "content": "Beds hold soil."},
]


def test_past_turns() -> None:
    assert past_turns(HISTORY) == TURNS


def test_messages_with_a_selected_node() -> None:
    messages = build_messages(LATEST, "and now?", HISTORY, "Beds", "p1")
    assert messages[0]["role"] == "system"
    assert '"Garden"' in messages[0]["content"]
    assert "Beds" in messages[0]["content"]
    assert "has selected this part" in messages[0]["content"]
    assert messages[1:-1] == TURNS
    assert messages[-1] == {"role": "user", "content": "[about: Beds] and now?"}


def test_messages_with_nothing_selected() -> None:
    unfocused = build_messages(LATEST, "hi", [])
    assert len(unfocused) == 2
    assert "has selected this part" not in unfocused[0]["content"]
    assert "Nothing is selected" in unfocused[0]["content"]


def test_past_turns_are_capped() -> None:
    many = [{"feedback": f"r{i} Note: n{i}"} for i in range(MAX_TURNS + 5)]
    assert len(past_turns(many)) == 2 * MAX_TURNS
    assert past_turns(many)[-1]["content"] == f"r{MAX_TURNS + 4}"


def test_map_text_and_selected_path() -> None:
    # As the system text shows them.
    tree = {
        "plan": {"progression": {"steps": [
            {"id": "p1", "label": "Sample", "children": [
                {"id": "p2", "label": "src", "children": [
                    {"id": "p4", "label": "main.py", "children": []},
                ]},
                {"id": "p3", "label": "readme.txt", "children": []},
            ]},
        ]}},
    }
    system = build_messages(tree, "hi", [], "main.py", "p4")[0]["content"]
    assert "readme.txt" in system
    assert "what it contains):\nSample\n  src\n    main.py" in system
    loose = build_messages(tree, "hi", [], "loose", None)[0]["content"]
    assert "what it contains):\nloose" in loose
    empty = build_messages({"plan": {}}, "hi", [])[0]["content"]
    assert "The project has no parts yet." in empty


def test_selected_day_of_changes() -> None:
    # Listed in the background, tagged on turns.
    tape = [
        {"feedback": "Added step: Beds", "event": "node_added", "created_at": "2026-09-20T12:00:00"},
        {"feedback": "Two beds. Note: what changed?", "event": "chat",
         "created_at": "2026-09-20T13:00:00", "focus_day": "2026-09-20"},
    ]
    day = build_messages(LATEST, "and?", tape, focus_day="2026-09-20")
    assert "selected the changes on 20 Sep" in day[0]["content"]
    assert "Added step: Beds" in day[0]["content"]
    assert "Nothing is selected" not in day[0]["content"]
    assert day[1]["content"] == "[about: changes on 20 Sep] what changed?"
    assert day[-1]["content"] == "[about: changes on 20 Sep] and?"


def test_renamed_node_in_past_turns() -> None:
    # Past turns name the node as it is called now, and what it was
    # called then.
    renamed_tree = {"name": "Garden", "plan": {"progression": {"steps": [
        {"id": "p1", "label": "Flower beds", "children": []},
    ]}}}
    talk = [{"feedback": "Beds hold soil. Note: what is this",
             "map_focus": "Beds", "focus_step_id": "p1"}]
    later = build_messages(renamed_tree, "and now?", talk)
    assert later[1] == {"role": "user",
                        "content": "[about: Flower beds (then called Beds)] what is this"}
    assert past_turns(talk, {"p1": "Beds"})[0]["content"] == "[about: Beds] what is this"
