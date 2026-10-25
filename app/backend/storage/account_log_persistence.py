"""
An account's own log — data/accounts/{account_id}/events.jsonl: what the
account has and has had (a project made, archived, sent, ...), one line
each, appended and never rewritten. What happens inside a project is
that project's log (project_persistence.py).

A line is {at, user_id, event, project_id, project, from_account?,
to_account?}: accounts by id only, the project's name as it was. Which
lines are written, and when, is account_log.py's (project/panes/create/).
"""

# Contents
#  1. Account logs (accounts/{id}/events.jsonl)
#      - account_log_path()
#      - append_account_event() / load_account_events() / delete_account_log()

import shutil
from pathlib import Path

from backend.storage.jsonl import append_jsonl, read_jsonl
from backend.storage.paths import data_dir

# ============================================================
# 1. Account logs (accounts/{id}/events.jsonl)
# ============================================================


def account_log_path(account_id: str) -> Path:
    """accounts/{id}/events.jsonl under data/, or under the visitor's
    demo sandbox (paths.data_dir())."""
    return data_dir() / "accounts" / account_id / "events.jsonl"


def append_account_event(account_id: str, event: dict) -> None:
    """Add one line to the account's log."""
    append_jsonl(account_log_path(account_id), event)


def load_account_events(account_id: str) -> list[dict]:
    """The account's log, oldest first; [] when it has none yet."""
    return read_jsonl(account_log_path(account_id))


def delete_account_log(account_id: str) -> None:
    """Erase the account's log, for an account deleted for good."""
    shutil.rmtree(account_log_path(account_id).parent, ignore_errors=True)
