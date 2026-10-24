"""Checks for how ids are made and shown."""

import uuid

import pytest

from backend.identity import (
    new_account_id,
    new_change_id,
    new_node_id,
    new_project_id,
    short_id,
)


@pytest.mark.parametrize(
    "make", [new_node_id, new_change_id, new_project_id, new_account_id]
)
def test_an_id_is_a_bare_random_uuid(make) -> None:
    made = make()
    assert uuid.UUID(made).version == 4
    assert str(uuid.UUID(made)) == made  # the standard written form, nothing in front


def test_ids_do_not_repeat_or_follow_an_order() -> None:
    ids = [new_node_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    assert ids != sorted(ids)


def test_short_id_is_the_first_eight_characters() -> None:
    made = new_node_id()
    assert short_id(made) == made[:8]
