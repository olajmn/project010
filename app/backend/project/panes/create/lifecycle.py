"""
A project's lifecycle: mint one, abandon one, restore or erase.

Identity and current state stay in resolver.py - this module only
writes. Mint is create_project() — a name and an empty canvas, no
engine. Renaming the label is rename.py. Cancelling never does.
The account is given at birth; changing it later is
project_account.set_project_user().
"""

# Contents
#  1. Creation
#      - create_project()
#      - next_default_name()
#
#  2. Cancellation / restore / delete
#      - cancel_project() / restore_project() / delete_project()

import re

from backend.project.node import nodes_of
from backend.project.panes.create.account_log import record_project_event
from backend.project.panes.create.resolver import (
    get_latest_for_all_projects,
    get_latest_for_project,
)
from backend.storage.accounts_persistence import get_account
from backend.storage.project_persistence import (
    delete_project as erase_project_store,
)
from backend.storage.project_persistence import (
    save_project,
)

# ============================================================
# 1. Creation
# ============================================================


def create_project(typed_text: str, account_id: str) -> dict | None:
    """
    Mint a project: a name and an empty canvas. No engine.

    The typed text is only a label. The tree arrives afterwards —
    built by hand, pasted, or walked in from a folder. Empty text gets
    `next_default_name()`, so every client names the same way.

    A project is always held: returns None, and saves nothing, unless
    `account_id` names a live, unarchived account.
    """
    account = get_account(account_id)
    if account is None or account.get("archived"):
        return None
    name = typed_text.strip() or next_default_name(account_id)
    record = save_project(
        name,
        [],
        account_id=account_id,
        event="created",
    )
    record_project_event("project_created", record)
    return record


# Bare "New project" and legacy "New project #4" count too.
_DEFAULT_NAME_RE = re.compile(r"^new project(?: #?(\d+))?$", re.IGNORECASE)


def next_default_name(account_id: str | None) -> str:
    """
    Next unused `New project N` among this account's active projects.

    Counts per account, so each seat starts at 1; archived projects
    don't count, matching what the sidebar shows.
    """
    highest = 0
    for record in get_latest_for_all_projects():
        if record.get("account_id") != account_id:
            continue
        if record.get("cancelled"):
            continue
        match = _DEFAULT_NAME_RE.match((record.get("name") or "").strip())
        if match:
            highest = max(highest, int(match.group(1) or 1))
    return f"New project {highest + 1}"


# ============================================================
# 2. Cancellation / restore / delete
# ============================================================


def cancel_project(project_id: str) -> dict | None:
    """
    Mark a project as cancelled (archived). Preserves `nodes` and
    `account_id` from the latest record exactly as they were, so the
    project's own data/history is never lost, only marked as no longer
    being pursued (still visible in full in the project's timeline, same
    as any other project).

    Returns the newly saved record, or None if `project_id` doesn't
    resolve to any project.

    Requesting cancellation on an already-cancelled project is a genuine
    no-op - returns `latest` unchanged rather than appending an
    identical record (same idiom as set_project_user()).
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if latest.get("cancelled"):
        return latest

    record = save_project(
        latest["name"],
        nodes_of(latest),
        feedback="Cancelled",
        project_id=latest["project_id"],
        account_id=latest.get("account_id"),
        cancelled=True,
        event="archived",
    )
    record_project_event("project_archived", record)
    return record


def restore_project(project_id: str) -> dict | None:
    """Clear cancelled so the project is active again, with the account
    that held it all along.

    No-op if already live. Returns None if missing.
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if not latest.get("cancelled"):
        return latest

    record = save_project(
        latest["name"],
        nodes_of(latest),
        feedback="Restored",
        project_id=latest["project_id"],
        account_id=latest.get("account_id"),
        cancelled=False,
        event="restored",
    )
    record_project_event("project_restored", record)
    return record


def delete_project(project_id: str) -> bool:
    """Permanently erase the project store. True if something was removed.
    The account that held it keeps a line saying so (account_log.py)."""
    latest = get_latest_for_project(project_id)
    if not erase_project_store(project_id):
        return False
    if latest is not None:
        record_project_event("project_deleted", latest)
    return True
