"""
Build a data folder (accounts, projects, saved trees) from story.py by
running each step through the app's own functions, with a clock set to
the step's time. Every map edit therefore saves the same change record
it would in use, and the log replays to each tree (changes/replay.py).

Dates move forward by whole weeks so the story ends on the last working
day before today; rerun it when they grow old. Ids are new on every run.

Run from app/, into a folder that does not exist yet:
    python -m backend.seed.build demo_seed.new
"""

# Contents
#  1. Time
#      - WRITTEN_FOR, LOCAL
#      - Clock
#
#  2. Running the story
#      - build()
#      - _run_project()
#      - _do()
#
#  3. Helpers
#      - _use_clock()
#      - _node_id()
#
#  4. Entry point
#      - main()

import random
import re
import secrets
import shutil
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.project.changes.replay import mismatch
from backend.project.node import steps_of
from backend.project.panes.canvas.edit_map import (
    add_map_node,
    import_map_outline,
    move_map_node,
    remove_map_node,
    rename_map_node,
)
from backend.project.panes.chat.reply import save_chat_turn
from backend.project.panes.create.lifecycle import create_project
from backend.project.saved_trees.saved_trees import save_tree_from_node
from backend.seed import story
from backend.storage import paths, sandboxes
from backend.storage.accounts_persistence import save_account
from backend.storage.project_persistence import load_current

# ============================================================
# 1. Time
# ============================================================

# The day the story's dates are written for; a later run shifts them.
WRITTEN_FOR = date(2026, 10, 24)

# Story times are local working hours.
LOCAL = ZoneInfo("Europe/Oslo")

_DATE_IN_TEXT = re.compile(r"\{date:(\d{4}-\d{2}-\d{2})\}")


class Clock:
    """The time every save reads (in place of paths.now_utc while a
    build runs), moved forward by the story."""

    def __init__(self, shift: timedelta) -> None:
        self.shift = shift
        self.moment = datetime.min.replace(tzinfo=UTC)

    def day(self, written: str) -> date:
        return date.fromisoformat(written) + self.shift

    def set(self, day: date, clock: time) -> None:
        local = datetime.combine(day, clock, tzinfo=LOCAL)
        if local.astimezone(UTC) < self.moment:
            raise ValueError(f"{day} {clock}: earlier than the step before it")
        self.moment = local.astimezone(UTC)

    def now_utc(self) -> str:
        return self.moment.isoformat(timespec="milliseconds")

    def at(self, moment: datetime) -> str:
        return moment.isoformat(timespec="milliseconds")


# ============================================================
# 2. Running the story
# ============================================================


def build(out: Path, today: date) -> None:
    """Write the story's data into `out`, which must not exist yet."""
    if out.exists():
        raise SystemExit(f"{out} already exists; build into a new folder")
    clock = Clock(timedelta(weeks=(today - WRITTEN_FOR).days // 7))
    restore_clock = _use_clock(clock)

    # Storage writes wherever the current sandbox points (sandboxes.py).
    real_root = sandboxes.ROOT
    sandboxes.ROOT = Path(tempfile.mkdtemp(prefix="project010-seed-"))
    build_id = secrets.token_hex(8)
    folder = sandboxes.ROOT / build_id
    folder.mkdir()
    sandboxes.use(build_id)
    try:
        clock.set(clock.day(story.PROJECTS[0][1][0][0]), time(8, 20))
        account_id = save_account(story.ACCOUNT)["id"]
        for name, days in story.PROJECTS:
            project_id = _run_project(name, days, account_id, clock)
            why = mismatch(folder / "projects" / project_id)
            if why:
                raise ValueError(f"{name}: {why}")
        shutil.move(str(folder), str(out))
    finally:
        sandboxes.use(None)
        shutil.rmtree(sandboxes.ROOT, ignore_errors=True)
        sandboxes.ROOT = real_root
        restore_clock()


def _run_project(name: str, days: list, account_id: str, clock: Clock) -> str:
    # Projects overlap in time; steps only move forward within one.
    clock.moment = datetime.min.replace(tzinfo=UTC)
    project_id = ""
    for written, actions in days:
        day = clock.day(written)
        # Same times on every run, different on every day.
        rng = random.Random(f"{name} {written}")
        minutes = 8 * 60 + 30 + rng.randint(0, 6 * 60)
        for action in actions:
            if action.get("at"):
                clock.set(day, time.fromisoformat(action["at"]))
            else:
                clock.set(day, time(minutes // 60, minutes % 60, rng.randint(0, 59)))
            minutes = clock.moment.astimezone(LOCAL).hour * 60
            minutes += clock.moment.astimezone(LOCAL).minute + rng.randint(4, 40)
            if action["do"] == "create":
                project_id = create_project(name, account_id)["project_id"]
            else:
                _do(action, load_current(project_id) or {}, clock)
    return project_id


def _do(action: dict, latest: dict, clock: Clock) -> None:
    """One story step on the project saved as `latest`."""
    do = action["do"]
    if do == "paste":
        parent = _node_id(latest, action["under"]) if action["under"] else None
        # Read as plain indented lines, as Paste does with unwrap off.
        import_map_outline(latest, action["outline"], parent, unwrap=False)
    elif do == "add":
        parent = _node_id(latest, action["under"]) if action["under"] else None
        add_map_node(latest, action["label"], parent)
    elif do == "rename":
        rename_map_node(latest, _node_id(latest, action["path"]), action["label"])
    elif do == "move":
        move_map_node(latest, _node_id(latest, action["path"]), action["direction"])
    elif do == "remove":
        remove_map_node(latest, _node_id(latest, action["path"]))
    elif do == "save_tree":
        save_tree_from_node(latest, _node_id(latest, action["path"]))
    elif do == "chat":
        about = action["about"]
        node_id = _node_id(latest, about) if about else None
        focus_day = action["focus_day"]
        reply = _DATE_IN_TEXT.sub(
            lambda m: f"{clock.day(m.group(1)).day} {clock.day(m.group(1)):%b}",
            action["reply"],
        )
        # The message is sent a moment before the reply is saved.
        sent = clock.at(clock.moment - timedelta(seconds=12))
        save_chat_turn(
            latest,
            action["message"],
            reply,
            sent,
            map_focus=about.split("/")[-1] if about else None,
            focus_step_id=node_id,
            focus_day=clock.day(focus_day).isoformat() if focus_day else None,
        )
    else:
        raise ValueError(f"unknown story step: {do}")


# ============================================================
# 3. Helpers
# ============================================================


def _use_clock(clock: Clock) -> Callable[[], None]:
    """Point every module that imported paths.now_utc at the clock;
    returns what puts the real one back."""
    real = paths.now_utc
    patched = [
        m for m in list(sys.modules.values()) if getattr(m, "now_utc", None) is real
    ]
    for module in patched:
        module.now_utc = clock.now_utc  # type: ignore[attr-defined]

    def restore() -> None:
        for module in patched:
            module.now_utc = real  # type: ignore[attr-defined]

    return restore


def _node_id(latest: dict, path: str) -> str:
    """The id of the node at `path` (labels from the top, "/" between)."""
    siblings = steps_of(latest)
    node: dict | None = None
    for label in path.split("/"):
        node = next((s for s in siblings if s.get("label") == label), None)
        if node is None:
            raise ValueError(f"no node at {path} (stopped at {label})")
        siblings = node.get("children") or []
    assert node is not None
    return str(node["id"])


# ============================================================
# 4. Entry point
# ============================================================


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m backend.seed.build <new folder>")
        return 2
    build(Path(argv[0]), date.today())
    print(f"built {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
