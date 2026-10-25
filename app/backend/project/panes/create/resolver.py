"""
Read and interpret project history.

This module does not store anything - it reads via project_persistence
and answers, by project_id:

- What is the full event tape for this project?
- What is the current SoT record for this project?
- What is the current record for every project that exists?

Whether a project counts as active or archived, and how projects
get grouped or sorted for display, is board-building logic, not project
identity.

A project's id is made in backend/identity/ when it is first saved
(project_persistence.save_project()); identity is that id, not the
project's display name (docs/05-decisions.md #81).
"""

from datetime import datetime

from backend.storage.project_persistence import (
    load_all_currents,
    load_current,
    load_project_history,
)

# Timestamp handling


def created_at_key(record: dict) -> datetime:
    """A record's `created_at` as a datetime, to sort by. Every record
    holds UTC with its offset (paths.now_utc()). Public because
    timeline.py and api/answers_to_browser.py sort by it."""
    return datetime.fromisoformat(record["created_at"])


# Read one project


def get_history_for_project(project_id: str) -> list[dict]:
    """
    Return every record for one project_id, oldest first: that
    project's events tape (data/projects/{id}/events.jsonl).
    """
    return load_project_history(project_id)


def get_latest_for_project(project_id: str) -> dict | None:
    """Return the current SoT record for one project_id, or None."""
    return load_current(project_id)


def get_latest_for_all_projects() -> list[dict]:
    """
    Return the current SoT record for every project_id - one
    project, one record.
    """
    return load_all_currents()
