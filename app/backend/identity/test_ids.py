"""Checks for how ids are made and shown."""

import uuid

import pytest

from backend.identity import kind_of, new_change_id, new_node_id, short_id


@pytest.mark.parametrize(
    "make, kind", [(new_node_id, "node"), (new_change_id, "change")]
)
def test_an_id_is_its_kind_and_a_random_uuid(make, kind) -> None:
    made = make()
    prefix, _, rest = made.partition("_")
    assert prefix == kind
    assert uuid.UUID(rest).version == 4
    assert str(uuid.UUID(rest)) == rest  # the standard written form
    assert kind_of(made) == kind


def test_ids_do_not_repeat_or_follow_an_order() -> None:
    ids = [new_node_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    assert ids != sorted(ids)


def test_short_id_is_eight_characters_after_the_kind() -> None:
    made = new_node_id()
    assert short_id(made) == made.removeprefix("node_")[:8]
    # Ids made before kinds had a prefix are shortened the same way.
    assert short_id("3f9c2a71-8b4e-4d10-a6f2-91c0e7b45d38") == "3f9c2a71"
    assert short_id("p2") == "p2"
    assert kind_of("3f9c2a71-8b4e") is None
