"""
An account's own log: one line each time a project it holds is made,
archived, brought back, or deleted for good, and on both accounts when a
project is sent from one to the other. What happens inside a project is
that project's log. Where the lines are kept is
storage/account_log_persistence.py.
"""

# Contents
#  1. Writing
#      - record_project_event()
#      - record_transfer()
#
#  2. Reading
#      - KINDS
#      - account_log()

from backend.storage.account_log_persistence import (
    append_account_event,
    load_account_events,
)
from backend.storage.paths import DEFAULT_USER_ID, now_utc

# ============================================================
# 1. Writing
# ============================================================


def _line(event: str, project: dict, **accounts: str) -> dict:
    return {
        "at": now_utc(),
        "user_id": DEFAULT_USER_ID,
        "event": event,
        "project_id": project["project_id"],
        "project": project.get("name", ""),
        **accounts,
    }


def record_project_event(event: str, project: dict) -> None:
    """One line on the account holding `project` (a saved project
    record): `project_created`, `project_archived`, `project_restored`,
    or `project_deleted`."""
    account_id = project.get("account_id")
    if account_id:
        append_account_event(account_id, _line(event, project))


def record_transfer(project: dict, from_account: str, to_account: str) -> None:
    """A project sent between accounts: `project_sent` on the one it
    left, `project_received` on the one it went to, each naming both."""
    accounts = {"from_account": from_account, "to_account": to_account}
    append_account_event(from_account, _line("project_sent", project, **accounts))
    append_account_event(to_account, _line("project_received", project, **accounts))


# ============================================================
# 2. Reading
# ============================================================

# Each line's `event` → the kind shown before it in an account's log.
KINDS = {
    "project_created": "Created",
    "project_archived": "Archived",
    "project_restored": "Restored",
    "project_deleted": "Deleted",
    "project_sent": "Sent",
    "project_received": "Received",
}


def account_log(account_id: str) -> list[dict]:
    """The account's log, oldest first, in the shape of a project's
    timeline entries ({at, project_id, project, event, kind, text}), so a
    details page draws both the same way. A transfer also carries
    `account`, the other account's id; the page names it."""
    entries = []
    for line in load_account_events(account_id):
        event = line.get("event") or "other"
        entry = {
            "at": line.get("at"),
            "project_id": line.get("project_id"),
            "project": line.get("project", ""),
            "event": event,
            "kind": KINDS.get(event, "Other"),
            "text": "",
        }
        if event == "project_sent":
            entry["account"] = line.get("to_account")
        elif event == "project_received":
            entry["account"] = line.get("from_account")
        entries.append(entry)
    return entries
