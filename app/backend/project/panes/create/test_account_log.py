"""An account's own log, through the functions that write it: making,
archiving, restoring, deleting, and sending a project. Storage points at
a temporary folder; no model.
"""

import pytest

from backend.project.panes.create.account_log import account_log
from backend.project.panes.create.lifecycle import (
    cancel_project,
    create_project,
    delete_project,
    restore_project,
)
from backend.project.panes.create.project_account import set_project_user
from backend.project.panes.create.rename import rename_project
from backend.storage import accounts_persistence as ap
from backend.storage import paths as storage_paths
from backend.storage import project_persistence as pp
from backend.storage.account_log_persistence import (
    append_account_event,
    load_account_events,
)


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_paths, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(ap, "ACCOUNTS_FILE", tmp_path / "accounts.json")
    return tmp_path


def kinds(account_id: str) -> list[str]:
    return [e["kind"] for e in account_log(account_id)]


def test_a_new_account_has_an_empty_log() -> None:
    assert account_log(ap.save_account("A")["id"]) == []


def test_a_project_made_archived_restored_and_deleted() -> None:
    a = ap.save_account("A")["id"]
    pid = create_project("House", a)["project_id"]
    cancel_project(pid)
    restore_project(pid)
    rename_project(pid, "Home")  # inside the project: its own log, not this one
    cancel_project(pid)
    delete_project(pid)
    assert kinds(a) == ["Created", "Archived", "Restored", "Archived", "Deleted"]
    log = account_log(a)
    # The project is gone, its lines stay, with the name it had each time.
    assert [e["project"] for e in log] == ["House", "House", "House", "Home", "Home"]
    assert {e["project_id"] for e in log} == {pid}
    assert all(e["text"] == "" and e["at"] for e in log)


def test_repeating_a_no_op_writes_nothing() -> None:
    a = ap.save_account("A")["id"]
    pid = create_project("House", a)["project_id"]
    restore_project(pid)  # not archived
    set_project_user(pid, a)  # already its holder
    assert kinds(a) == ["Created"]


def test_a_transfer_is_a_line_on_both_accounts() -> None:
    a, b = (ap.save_account(t)["id"] for t in ("A", "B"))
    pid = create_project("House", a)["project_id"]
    set_project_user(pid, b)
    sent, received = account_log(a)[-1], account_log(b)[-1]
    assert (sent["kind"], sent["account"]) == ("Sent", b)
    assert (received["kind"], received["account"]) == ("Received", a)
    assert sent["project_id"] == received["project_id"] == pid
    # Both saved lines name both sides.
    for line in (load_account_events(a)[-1], load_account_events(b)[-1]):
        assert (line["from_account"], line["to_account"]) == (a, b)


def test_an_unknown_line_reads_as_other() -> None:
    append_account_event("a1", {"event": "something_new", "project": "P"})
    assert kinds("a1") == ["Other"]
