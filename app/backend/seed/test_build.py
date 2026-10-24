"""Checks for the seed build: the whole story runs through the app's
edits, each project's log replays to its tree, and dates shift by
whole weeks."""

import json
from datetime import date

from backend.seed.build import WRITTEN_FOR, build
from backend.seed.story import PROJECTS
from backend.storage import paths


def test_the_story_builds_and_replays(tmp_path) -> None:
    # build() itself refuses a project whose log does not replay.
    out = tmp_path / "seed"
    build(out, WRITTEN_FOR)
    names = {
        json.loads((d / "current.json").read_text())["name"]
        for d in (out / "projects").iterdir()
    }
    assert names == {name for name, _ in PROJECTS}
    assert paths.now_utc.__module__ == "backend.storage.paths"


def test_dates_move_by_whole_weeks(tmp_path) -> None:
    out = tmp_path / "seed"
    build(out, date(2026, 11, 3))
    account = json.loads((out / "accounts.json").read_text())[0]
    # 10 days later is one whole week: the first day is still a Monday.
    assert account["created_at"].startswith("2026-08-10")
