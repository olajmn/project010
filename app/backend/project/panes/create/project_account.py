"""
Which account holds a project: send one to another account, and tell
whether an account still holds any.

Identity writes, not reasoning. Judgment does not own this.
"""

from backend.project.node import nodes_of
from backend.project.panes.create.account_log import record_transfer
from backend.project.panes.create.resolver import (
    get_latest_for_all_projects,
    get_latest_for_project,
)
from backend.storage.accounts_persistence import get_account
from backend.storage.project_persistence import save_project


def set_project_user(project_id: str, account_id: str | None) -> dict | None:
    """
    Send a project to another account. A project is always held, so
    there is no way to take it from its account without giving it to
    another one.

    Unlike the chat's reply() (which takes an already-resolved `latest`
    record), this resolves `project_id` itself, since the route calling
    it has no other reason to look the record up first.

    Returns the newly saved record, or None if the change is
    rejected - never partially applied, and never raises for an
    ordinary bad input:
    - `project_id` doesn't resolve to any project.
    - `account_id` is None, or no such account exists.

    Sending to the account that already holds it is a no-op - returns
    `latest` unchanged rather than appending an identical record.
    Archived projects and archived accounts can send and receive: the
    holder changes, the archived state (`cancelled`) is carried over
    as it was.

    Preserves `nodes` from the latest record exactly as they were - this
    changes which account the project belongs to, nothing about the map
    itself.
    """
    latest = get_latest_for_project(project_id)
    if latest is None or account_id is None:
        return None
    if account_id == latest.get("account_id"):
        return latest
    account = get_account(account_id)
    if account is None:
        return None

    record = save_project(
        latest["name"],
        nodes_of(latest),
        feedback=f"Moved to account: {account['text']}",
        project_id=latest["project_id"],
        account_id=account_id,
        cancelled=bool(latest.get("cancelled")),
        event="owner_changed",
    )
    if latest.get("account_id"):
        record_transfer(record, latest["account_id"], account_id)
    return record


def holds_projects(account_id: str) -> bool:
    """
    True if any project, archived or not, is held by this account. Such
    an account cannot be deleted for good: its projects would be held
    by nothing.
    """
    return any(
        latest.get("account_id") == account_id
        for latest in get_latest_for_all_projects()
    )
