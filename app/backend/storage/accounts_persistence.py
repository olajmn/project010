"""
Accounts — data/accounts.json. An account's id comes from
backend/identity/.

Project current + events live in project_persistence.py. Shared roots
(DATA_DIR, now_utc, …) live in paths.py.

An account is a plain {id, text, created_at} record — no history.
Projects may reference one via optional account_id. Archiving mutates
the account record in place; detaching projects is a higher-level decision
(project_account.archive_account()).

Every record also carries a stub user_id (DEFAULT_USER_ID) — the
operator of this app, not the multi-account filter.

Permanent delete leaves a tombstone ({id, user_id, deleted, deleted_at})
so the deletion stays on record: closed projects keep their account_id,
which names that account and no other. Tombstones are invisible to every
other function here.
"""

# Contents
#  1. Accounts (accounts.json)
#      - save_account() / load_accounts() / get_account() / rename_account()
#      - archive_account() / restore_account() / delete_account()

import json
from pathlib import Path

from backend.identity import new_account_id
from backend.storage import sandboxes
from backend.storage.paths import (
    DATA_DIR,
    DEFAULT_USER_ID,
    ensure_data_dir,
    now_utc,
)

ACCOUNTS_FILE = DATA_DIR / "accounts.json"


# ============================================================
# 1. Accounts (accounts.json)
# ============================================================


def _accounts_file() -> Path:
    """ACCOUNTS_FILE, or accounts.json in the visitor's demo sandbox."""
    sandbox = sandboxes.current()
    return sandbox / "accounts.json" if sandbox else ACCOUNTS_FILE


def _load_all_accounts() -> list[dict]:
    """Read every saved account (tombstones included)."""
    path = _accounts_file()
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            accounts = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{path} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e
    return accounts


def _save_all_accounts(accounts: list[dict]) -> None:
    """Write the full list of accounts — atomic temp-file rename."""
    ensure_data_dir()
    path = _accounts_file()
    tmp_file = path.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    tmp_file.replace(path)


def _live(accounts: list[dict]) -> list[dict]:
    """Accounts minus delete tombstones."""
    return [a for a in accounts if not a.get("deleted")]


def save_account(text: str) -> dict:
    """
    Create an account and persist it — a tenant slot projects can
    optionally reference via account_id.

    No history, no revisions: a single mutable fact, not a chain.

    Returns the record that was saved.
    """
    accounts = _load_all_accounts()
    record = {
        "id": new_account_id(),
        "user_id": DEFAULT_USER_ID,
        "text": text,
        "created_at": now_utc(),
    }
    accounts.append(record)
    _save_all_accounts(accounts)
    return record


def load_accounts() -> list[dict]:
    """Return every saved account, oldest first."""
    return _live(_load_all_accounts())


def get_account(account_id: str) -> dict | None:
    """Return the account with this id, or None if missing."""
    for account in _live(_load_all_accounts()):
        if account["id"] == account_id:
            return account
    return None


def rename_account(account_id: str, text: str) -> dict | None:
    """
    Set the display label on an account. Empty / whitespace becomes
    the default "user" so the UI falls back to account <short id>. Returns the
    record, or None if id doesn't resolve. Archived accounts can still be
    renamed (label only).
    """
    label = (text or "").strip() or "user"
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == account_id:
            account["text"] = label
            _save_all_accounts(accounts)
            return account
    return None


def archive_account(account_id: str) -> dict | None:
    """
    Mark an account as archived. Mutates the existing record in
    place. Returns the record, or None if id doesn't resolve. Archiving
    an already-archived account is a no-op.

    Never touches project files — a project's account_id is left as-is.
    """
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == account_id:
            if account.get("archived"):
                return account
            account["archived"] = True
            account["archived_at"] = now_utc()
            _save_all_accounts(accounts)
            return account
    return None


def restore_account(account_id: str) -> dict | None:
    """Clear archived on an account. No-op if already live. None if missing."""
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == account_id:
            if not account.get("archived"):
                return account
            account.pop("archived", None)
            account.pop("archived_at", None)
            _save_all_accounts(accounts)
            return account
    return None


def delete_account(account_id: str) -> dict | None:
    """Replace an account with a tombstone (see module docstring).
    Returns the record as it was before deletion, or None if id doesn't
    resolve. Does not touch project files."""
    accounts = _load_all_accounts()
    for i, account in enumerate(accounts):
        if account["id"] == account_id and not account.get("deleted"):
            accounts[i] = {
                "id": account["id"],
                "user_id": account.get("user_id", DEFAULT_USER_ID),
                "deleted": True,
                "deleted_at": now_utc(),
            }
            _save_all_accounts(accounts)
            return account
    return None
