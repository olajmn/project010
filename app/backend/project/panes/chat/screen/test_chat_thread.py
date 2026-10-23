"""thread_messages() only - no model call."""

from backend.project.panes.chat.screen.chat_thread import thread_messages


def test_only_chat_turns_show() -> None:
    # Only chat turns show: the first record, map edits, and other saved
    # lines without "<reply> Note: <note>" are left to Status.
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
            "feedback": "Sure. Note: what next?",
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
            "feedback": "Added Kitchen. Note: /add Kitchen",
            "event": "chat",
        },
    ]
    assert thread_messages(added)[1] == {"role": "agent", "text": "Added Kitchen."}


def test_map_focus_tags_each_turn() -> None:
    # map_focus tags each turn so the UI can frame a focused stretch.
    focused = thread_messages(
        [
            {
                "feedback": "A room. Note: what is this?",
                "map_focus": "Rooms",
                "focus_step_id": "p1",
            },
            {"feedback": "Paint. Note: and now?"},
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
        [{"feedback": "Two edits. Note: what changed?", "focus_day": "2026-09-27"}]
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
            {"feedback": "Ok. Note: hi", "sent_at": "t1", "created_at": "t2"},
        ]
    )
    assert timed[0]["at"] == "t1" and timed[1]["at"] == "t2"


def test_rename_notes() -> None:
    # Renaming a node that was talked about adds a note in its conversation;
    # renaming one that never was adds nothing.
    renamed = thread_messages(
        [
            {
                "feedback": "Outside. Note: what is this?",
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
