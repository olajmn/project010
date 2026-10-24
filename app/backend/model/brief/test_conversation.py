"""Checks for build_messages() / past_turns() - no model call."""

from backend.model.brief.conversation import (
    MAX_TURNS,
    build_messages,
    past_turns,
)

LATEST = {
    "name": "Garden",
    "plan": {
        "progression": {
            "steps": [
                {"id": "p1", "label": "Beds", "children": []},
            ]
        }
    },
}
HISTORY = [
    {"feedback": None},  # first record: no turn
    {"feedback": "Zoomed into: Beds"},  # map edit: no turn
    {"event": "chat", "reply": "Sounds good.", "message": "hello"},
    {
        "event": "chat",
        "reply": "Beds hold soil.",
        "message": "what is this",
        "map_focus": "Beds",
    },
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
    many = [
        {"event": "chat", "reply": f"r{i}", "message": f"n{i}"}
        for i in range(MAX_TURNS + 5)
    ]
    assert len(past_turns(many)) == 2 * MAX_TURNS
    assert past_turns(many)[-1]["content"] == f"r{MAX_TURNS + 4}"


def test_map_text_and_selected_path() -> None:
    # As the system text shows them.
    tree = {
        "plan": {
            "progression": {
                "steps": [
                    {
                        "id": "p1",
                        "label": "Sample",
                        "children": [
                            {
                                "id": "p2",
                                "label": "src",
                                "children": [
                                    {"id": "p4", "label": "main.py", "children": []},
                                ],
                            },
                            {"id": "p3", "label": "readme.txt", "children": []},
                        ],
                    },
                ]
            }
        },
    }
    system = build_messages(tree, "hi", [], "main.py", "p4")[0]["content"]
    assert "readme.txt" in system
    assert "what it contains):\nSample\n  src\n    main.py" in system
    loose = build_messages(tree, "hi", [], "loose", None)[0]["content"]
    assert "Nothing is selected" in loose and "loose" not in loose
    empty = build_messages({"plan": {}}, "hi", [])[0]["content"]
    assert "The project has no parts yet." in empty


def test_selected_day_of_changes() -> None:
    # Listed in the background, tagged on turns.
    tape = [
        {
            "feedback": "Added step: Beds",
            "event": "node_added",
            "created_at": "2026-09-20T12:00:00",
        },
        {
            "reply": "Two beds.",
            "message": "what changed?",
            "event": "chat",
            "created_at": "2026-09-20T13:00:00",
            "focus_day": "2026-09-20",
        },
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
    renamed_tree = {
        "name": "Garden",
        "plan": {
            "progression": {
                "steps": [
                    {"id": "p1", "label": "Flower beds", "children": []},
                ]
            }
        },
    }
    talk = [
        {
            "reply": "Beds hold soil.",
            "message": "what is this",
            "event": "chat",
            "map_focus": "Beds",
            "focus_step_id": "p1",
        }
    ]
    later = build_messages(renamed_tree, "and now?", talk)
    assert later[1] == {
        "role": "user",
        "content": "[about: Flower beds (then called Beds)] what is this",
    }
    assert (
        past_turns(talk, [{"id": "p1", "label": "Beds", "children": []}])[0]["content"]
        == "[about: Beds] what is this"
    )


def test_map_edit_with_note_in_its_text_is_not_a_turn() -> None:
    # Only lines saved as chat are turns, whatever a node is called.
    edit = {"feedback": "Added step: Site Note: walls", "event": "node_added"}
    assert past_turns([edit]) == []


def test_message_and_reply_are_kept_apart() -> None:
    # Saved in their own fields, so no text inside either can split them.
    turn = {
        "event": "chat",
        "message": "what now? Note: walls are wet",
        "reply": "Paint first. Note: let them dry.",
    }
    assert past_turns([turn]) == [
        {"role": "user", "content": "what now? Note: walls are wet"},
        {"role": "assistant", "content": "Paint first. Note: let them dry."},
    ]


# A house where Kitchen (p9) was removed and two parts share the label
# "Planning", one under Rooms and one under Garden (docs/05-decisions.md #76).
HOUSE = {
    "name": "House",
    "plan": {
        "progression": {
            "steps": [
                {
                    "id": "p1",
                    "label": "Rooms",
                    "children": [{"id": "p3", "label": "Planning", "children": []}],
                },
                {
                    "id": "p2",
                    "label": "Garden",
                    "children": [{"id": "p4", "label": "Planning", "children": []}],
                },
            ]
        }
    },
}


def _turn(message: str, label: str, step_id: str) -> dict:
    return {
        "event": "chat",
        "message": message,
        "reply": "ok",
        "map_focus": label,
        "focus_step_id": step_id,
    }


def test_past_turns_name_their_part_by_path_or_as_removed() -> None:
    history = [
        _turn("what goes here?", "Kitchen", "p9"),
        _turn("when do we start?", "Planning", "p3"),
        _turn("and this one?", "Planning", "p4"),
    ]
    user_lines = [
        m["content"]
        for m in build_messages(HOUSE, "next?", history)
        if m["role"] == "user"
    ]
    assert user_lines[:3] == [
        "[about: Kitchen (since removed)] what goes here?",
        "[about: Rooms / Planning] when do we start?",
        "[about: Garden / Planning] and this one?",
    ]


def test_selected_part_is_named_by_path() -> None:
    messages = build_messages(HOUSE, "and now?", [], "Planning", "p4")
    assert messages[-1]["content"] == "[about: Garden / Planning] and now?"


def test_selected_part_that_no_longer_exists_is_no_selection() -> None:
    messages = build_messages(HOUSE, "and now?", [], "Kitchen", "p9")
    assert "Nothing is selected" in messages[0]["content"]
    assert "Kitchen" not in messages[0]["content"]
    assert messages[-1]["content"] == "and now?"


def test_asking_about_a_removed_part_on_purpose() -> None:
    # From that part's own conversation: it stays the subject, marked gone.
    messages = build_messages(
        HOUSE, "can we still talk about this?", [], "Kitchen", "p9", about_removed=True
    )
    assert messages[-1]["content"] == (
        "[about: Kitchen (since removed)] can we still talk about this?"
    )
    system = messages[0]["content"]
    assert 'asking about "Kitchen", a part that was removed' in system
    assert "Nothing is selected" not in system


def _wide_tree(n: int) -> dict:
    steps = [{"id": f"p{i}", "label": f"Part {i}", "children": []} for i in range(n)]
    return {"name": "Big", "plan": {"progression": {"steps": steps}}}


def test_structure_has_no_fixed_line_cap() -> None:
    system = build_messages(_wide_tree(500), "hi", [])[0]["content"]
    assert "Part 499" in system and "Structure cut" not in system


def test_structure_cut_only_to_fit_and_says_so(monkeypatch) -> None:
    from backend.model.brief import conversation

    monkeypatch.setattr(conversation, "STRUCTURE_TOKENS", 100)
    system = build_messages(_wide_tree(500), "hi", [])[0]["content"]
    assert "Part 0" in system and "Part 499" not in system
    assert "of 500 parts are shown; the rest are left out" in system
