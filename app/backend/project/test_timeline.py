"""Checks for event_name() / to_event() / all_events() paging - no files,
no model.
"""

import backend.project.timeline as timeline
from backend.project.timeline import event_name, to_event


def test_event_name() -> None:
    # New lines carry `event`; it wins over the feedback text.
    assert event_name({"event": "renamed", "feedback": "Renamed: a → b"}) == "renamed"
    # Every saved line carries `event`; one without it is "other".
    assert event_name({"feedback": "Added node: roof"}) == "other"


def test_to_event() -> None:
    chat = to_event(
        {
            "project_id": "project_4",
            "reply": "Sure.",
            "message": "what next?",
            "created_at": "2026-09-25T18:00:00.000+00:00",
            "event": "chat",
        },
        "House",
    )
    assert chat == {
        "at": "2026-09-25T18:00:00.000+00:00",
        "project_id": "project_4",
        "project": "House",
        "event": "chat",
        "kind": "Chat",
        "text": "what next?",
    }
    created = to_event(
        {"project_id": "project_4", "feedback": None, "event": "created"}, "House"
    )
    assert (created["kind"], created["text"]) == ("Created", "")
    renamed = to_event(
        {
            "project_id": "project_4",
            "feedback": "Renamed: Hus → House",
            "event": "renamed",
        },
        "House",
    )
    assert (renamed["kind"], renamed["text"]) == ("Renamed", "Renamed: Hus → House")
    long = to_event(
        {"project_id": "project_4", "feedback": "Added node: " + "x" * 300}, "House"
    )
    assert long["text"].endswith("…") and len(long["text"]) == 161


def test_all_events_pages_newest_first(monkeypatch) -> None:
    # Offset skips what is already shown.
    lines = [
        {
            "project_id": "project_1",
            "event": "node_added",
            "feedback": f"Added node: {n}",
            "created_at": f"2026-09-2{n}T10:00:00",
        }
        for n in range(1, 6)
    ]
    monkeypatch.setattr(timeline, "load_history", lambda: lines)
    monkeypatch.setattr(
        timeline,
        "get_latest_for_all_projects",
        lambda: [{"project_id": "project_1", "name": "P"}],
    )

    def texts(events):
        return [e["text"] for e in events]

    assert texts(timeline.all_events(limit=2)) == ["Added node: 5", "Added node: 4"]
    assert texts(timeline.all_events(limit=2, offset=2)) == [
        "Added node: 3",
        "Added node: 2",
    ]
    assert texts(timeline.all_events(limit=2, offset=4)) == ["Added node: 1"]
    assert timeline.all_events(limit=2, offset=9) == []
