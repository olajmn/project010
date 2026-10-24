"""thread_messages() only - no model call."""

from backend.project.panes.chat.screen.chat_thread import thread_messages


def test_only_chat_turns_show() -> None:
    # Only chat turns show: the first record, map edits, and other saved
    # lines that are not chat turns are left to Status.
    rooms = {"progression": {"steps": [{"label": "Rooms"}]}}
    history = [
        {"name": "House", "plan": {}, "feedback": None, "event": "created"},
        {
            "name": "House",
            "plan": rooms,
            "feedback": "Added step: Rooms",
            "event": "node_added",
        },
        {
            "name": "House",
            "plan": rooms,
            "reply": "Sure.",
            "message": "what next?",
            "event": "chat",
        },
        {
            "name": "House",
            "plan": rooms,
            "feedback": "Inserted tree",
            "event": "tree_inserted",
        },
    ]
    assert thread_messages(history) == [
        {"role": "user", "text": "what next?"},
        {"role": "agent", "text": "Sure."},
    ]


def test_turn_that_changed_the_map() -> None:
    # A turn that changed the map (/add) still shows its reply, not a
    # summary of the map.
    added = [
        {
            "name": "House",
            "plan": {},
            "reply": "Added Kitchen.",
            "message": "/add Kitchen",
            "event": "chat",
        },
    ]
    assert thread_messages(added)[1] == {"role": "agent", "text": "Added Kitchen."}


def test_map_focus_tags_each_turn() -> None:
    # map_focus tags each turn so the UI can frame a focused stretch.
    focused = thread_messages(
        [
            {
                "reply": "A room.",
                "message": "what is this?",
                "event": "chat",
                "map_focus": "Rooms",
                "focus_step_id": "p1",
            },
            {"event": "chat", "reply": "Paint.", "message": "and now?"},
        ]
    )
    assert focused[0] == {
        "role": "user",
        "text": "what is this?",
        "focus": "Rooms",
        "focus_step_id": "p1",
    }
    assert focused[1]["focus"] == "Rooms"
    assert "focus" not in focused[2]
    assert focused[3] == {"role": "agent", "text": "Paint."}


def test_turn_about_a_day() -> None:
    # A turn about a day of changes carries focus_day, not a node focus.
    by_day = thread_messages(
        [
            {
                "event": "chat",
                "reply": "Two edits.",
                "message": "what changed?",
                "focus_day": "2026-09-27",
            }
        ]
    )
    assert by_day[0] == {
        "role": "user",
        "text": "what changed?",
        "focus_day": "2026-09-27",
    }
    assert by_day[1]["focus_day"] == "2026-09-27"


def test_at_times() -> None:
    # `at`: the user line prefers sent_at, the agent line uses created_at.
    timed = thread_messages(
        [
            {
                "event": "chat",
                "reply": "Ok.",
                "message": "hi",
                "sent_at": "t1",
                "created_at": "t2",
            },
        ]
    )
    assert timed[0]["at"] == "t1" and timed[1]["at"] == "t2"


def test_rename_notes() -> None:
    # Renaming a node that was talked about adds a note in its conversation;
    # renaming one that never was adds nothing.
    renamed = thread_messages(
        [
            {
                "reply": "Outside.",
                "message": "what is this?",
                "event": "chat",
                "map_focus": "Surroundings",
                "focus_step_id": "p6",
            },
            {
                "feedback": "Renamed step: Surroundings → Landscape",
                "event": "node_renamed",
                "focus_step_id": "p6",
                "created_at": "t3",
            },
            {
                "feedback": "Renamed step: Site → Plot",
                "event": "node_renamed",
                "focus_step_id": "p5",
            },
        ]
    )
    assert renamed[2] == {
        "role": "note",
        "text": "Renamed from “Surroundings” to “Landscape”",
        "focus": "Landscape",
        "focus_step_id": "p6",
        "at": "t3",
    }
    assert len(renamed) == 3


def test_map_edit_with_note_in_its_text_is_not_a_turn() -> None:
    # Only lines saved as chat are turns, whatever a node is called.
    edit = {"feedback": "Added step: Site Note: walls", "event": "node_added"}
    assert thread_messages([edit]) == []


def test_message_and_reply_are_kept_apart() -> None:
    # Saved in their own fields, so no text inside either can split them.
    turn = {
        "event": "chat",
        "message": "what now? Note: walls are wet",
        "reply": "Paint first. Note: let them dry.",
    }
    assert thread_messages([turn]) == [
        {"role": "user", "text": "what now? Note: walls are wet"},
        {"role": "agent", "text": "Paint first. Note: let them dry."},
    ]


def test_turns_about_a_removed_part_are_marked() -> None:
    steps = [{"id": "p1", "label": "Rooms", "children": []}]
    history = [
        {
            "event": "chat",
            "message": "a?",
            "reply": "b",
            "map_focus": "Kitchen",
            "focus_step_id": "p9",
        },
        {
            "event": "chat",
            "message": "c?",
            "reply": "d",
            "map_focus": "Rooms",
            "focus_step_id": "p1",
        },
    ]
    shown = thread_messages(history, steps)
    assert [m.get("removed") for m in shown] == [True, True, None, None]


def _turn_about(step_id: str, label: str) -> dict:
    return {
        "event": "chat",
        "message": "what belongs here?",
        "reply": "ok",
        "map_focus": label,
        "focus_step_id": step_id,
    }


def _contexts(steps: list, history: list) -> list:
    return [m.get("focus_context") for m in thread_messages(history, steps)[::2]]


def test_a_label_used_twice_shows_its_parent() -> None:
    steps = [
        {
            "id": "p1",
            "label": "Design",
            "children": [{"id": "p2", "label": "Concept", "children": []}],
        },
        {
            "id": "p3",
            "label": "Development",
            "children": [{"id": "p4", "label": "Concept", "children": []}],
        },
        {"id": "p5", "label": "Actors", "children": []},
    ]
    history = [
        _turn_about("p2", "Concept"),
        _turn_about("p4", "Concept"),
        _turn_about("p5", "Actors"),
    ]
    assert _contexts(steps, history) == ["Design", "Development", None]


def test_parents_with_the_same_label_show_one_level_more() -> None:
    steps = [
        {
            "id": "p1",
            "label": "Client A",
            "children": [
                {
                    "id": "p2",
                    "label": "Scope",
                    "children": [{"id": "p3", "label": "Fees", "children": []}],
                },
            ],
        },
        {
            "id": "p4",
            "label": "Architect A",
            "children": [
                {
                    "id": "p5",
                    "label": "Scope",
                    "children": [{"id": "p6", "label": "Fees", "children": []}],
                },
            ],
        },
    ]
    history = [_turn_about("p3", "Fees"), _turn_about("p6", "Fees")]
    assert _contexts(steps, history) == ["Client A / Scope", "Architect A / Scope"]


def test_turns_carry_their_full_path() -> None:
    # Shown when the pointer rests on a frame's title.
    steps = [
        {
            "id": "p1",
            "label": "Civic Centre",
            "children": [
                {
                    "id": "p2",
                    "label": "Design",
                    "children": [{"id": "p3", "label": "Concept", "children": []}],
                },
            ],
        },
    ]
    shown = thread_messages(
        [_turn_about("p3", "Concept"), _turn_about("p9", "Gone")], steps
    )
    assert [m.get("focus_path") for m in shown] == [
        "Civic Centre / Design / Concept",
        "Civic Centre / Design / Concept",
        None,
        None,
    ]
