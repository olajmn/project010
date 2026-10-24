"""
Small, direct checks for account persistence and per-project
current.json + events.jsonl under data/projects/{id}/, plus
create_project()'s default `New project N` naming, since it only reads
what storage holds.

Every test runs against its own temporary directory, never the real
data/: the `data_dir` fixture points the path constants there.
"""

import pytest

from backend.identity import kind_of
from backend.storage import accounts_persistence as ap
from backend.storage import paths as storage_paths
from backend.storage import project_persistence as pp


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_paths, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(ap, "ACCOUNTS_FILE", tmp_path / "accounts.json")
    return tmp_path


def _two_projects():
    """Two accounts; the first owns two projects (after one unassigned)."""
    pp.save_plan("Make a song", {"now": "Write one line"})
    user = ap.save_account("Health")
    second_user = ap.save_account("Grow as a musician")
    abs_project = pp.save_plan("Get visible abs", {"now": "..."}, account_id=user["id"])
    cardio_project = pp.save_plan(
        "Improve cardio", {"now": "..."}, account_id=user["id"]
    )
    return user, second_user, abs_project, cardio_project


def test_save_plan_writes_current_and_events() -> None:
    plain_record = pp.save_plan("Make a song", {"now": "Write one line"})
    assert plain_record["account_id"] is None, plain_record["account_id"]
    assert plain_record["name"] == "Make a song"
    assert "goal" not in plain_record
    pid = plain_record["project_id"]
    assert kind_of(pid) == "project"
    assert pp.current_path(pid).exists()
    assert pp.events_path(pid).exists()
    assert pp.current_path(pid).parent.name == pid  # the id is the folder
    assert "plan" in pp.load_current(pid)
    assert "plan" not in pp.load_project_events(pid)[0]
    assert pp.events_path(pid).read_text(encoding="utf-8").count("\n") == 1


def test_accounts_save_rename_and_ids() -> None:
    user = ap.save_account("Improve physical health and quality of life")
    assert user["text"] == "Improve physical health and quality of life"
    assert kind_of(user["id"]) == "account"
    assert ap.get_account(user["id"]) == user
    assert ap.get_account("account_none") is None
    renamed = ap.rename_account(user["id"], "Health")
    assert renamed is not None and renamed["text"] == "Health"
    assert ap.rename_account(user["id"], "  ")["text"] == "user"

    second_user = ap.save_account("Grow as a musician")
    assert second_user["id"] != user["id"]
    assert [u["id"] for u in ap.load_accounts()] == [user["id"], second_user["id"]]


def test_projects_of_one_account() -> None:
    user, _, abs_project, cardio_project = _two_projects()
    assert abs_project["account_id"] == cardio_project["account_id"] == user["id"]
    assert abs_project["project_id"] != cardio_project["project_id"]
    assert "account_n" not in abs_project  # no per-account counter
    assert "goal_id" not in abs_project
    assert "name" in abs_project
    assert "goal" not in abs_project
    assert "vision_id" not in abs_project
    assert pp.current_path(abs_project["project_id"]).exists()
    assert pp.current_path(cardio_project["project_id"]).exists()
    assert len(pp.load_history()) == 3
    assert len(pp.load_project_history(abs_project["project_id"])) == 1


def test_saving_again_appends_one_event() -> None:
    user, _, abs_project, cardio_project = _two_projects()
    pp.save_plan(
        "Get visible abs",
        {"now": "again"},
        project_id=abs_project["project_id"],
        account_id=user["id"],
        event="chat",
    )
    assert (
        pp.events_path(abs_project["project_id"])
        .read_text(encoding="utf-8")
        .count("\n")
        == 2
    )
    assert (
        pp.events_path(cardio_project["project_id"])
        .read_text(encoding="utf-8")
        .count("\n")
        == 1
    )
    assert pp.load_current(abs_project["project_id"])["plan"]["now"] == "again"


def test_owner_change_keeps_the_project_id() -> None:
    _, second_user, _, cardio_project = _two_projects()
    moved = pp.save_plan(
        "Improve cardio",
        {"now": "..."},
        project_id=cardio_project["project_id"],
        account_id=second_user["id"],
        event="owner_changed",
    )
    assert moved["project_id"] == cardio_project["project_id"]
    assert moved["account_id"] == second_user["id"]


def test_account_archive_restore_delete() -> None:
    seat = ap.save_account("Parked")
    ap.archive_account(seat["id"])
    assert ap.get_account(seat["id"])["archived"] is True
    restored = ap.restore_account(seat["id"])
    assert restored is not None and not restored.get("archived")
    ap.archive_account(seat["id"])
    removed = ap.delete_account(seat["id"])
    assert removed is not None and removed["id"] == seat["id"]
    assert ap.get_account(seat["id"]) is None
    assert seat["id"] not in [a["id"] for a in ap.load_accounts()]
    assert ap.delete_account(seat["id"]) is None
    assert ap.restore_account(seat["id"]) is None
    after = ap.save_account("After delete")
    assert after["id"] != seat["id"]  # a deleted id is never handed out again


def test_project_erase() -> None:
    gone = pp.save_plan("To erase", {"now": "x"}, account_id=None)
    assert pp.current_path(gone["project_id"]).exists()
    assert pp.delete_project(gone["project_id"]) is True
    assert not pp.current_path(gone["project_id"]).exists()
    assert pp.delete_project(gone["project_id"]) is False


def test_empty_create_name_becomes_next_new_project() -> None:
    from backend.project.panes.create.lifecycle import cancel_project, create_project

    a, b, c = "account_a", "account_b", "account_c"
    assert create_project("", a)["name"] == "New project 1"
    assert create_project("  ", a)["name"] == "New project 2"
    assert create_project("", b)["name"] == "New project 1"  # per account
    pp.save_plan("New project #7", {"now": "x"}, account_id=a)  # legacy form
    assert create_project("", a)["name"] == "New project 8"
    assert create_project("Typed", a)["name"] == "Typed"
    cancel_project(create_project("", c)["project_id"])
    assert create_project("", c)["name"] == "New project 1"  # archived don't count


def test_a_change_record_goes_to_the_log_not_the_current_state() -> None:
    change = {
        "id": "change_x",
        "op": "rename",
        "node_id": "node_1",
        "from": "A",
        "to": "B",
    }
    pid = pp.save_plan("P", {"now": "x"}, event="node_renamed", change=change)[
        "project_id"
    ]
    assert pp.load_project_events(pid)[-1]["change"] == change
    assert "change" not in pp.load_current(pid)
