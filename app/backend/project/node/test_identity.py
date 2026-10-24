"""Checks for how node ids are made and shown."""

import uuid

from backend.project.node import new_node_id, short_id


def test_a_node_id_is_a_random_uuid() -> None:
    node_id = new_node_id()
    assert uuid.UUID(node_id).version == 4
    assert str(uuid.UUID(node_id)) == node_id  # the standard written form


def test_ids_do_not_repeat_or_follow_an_order() -> None:
    ids = [new_node_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    assert ids != sorted(ids)


def test_short_id_is_the_first_eight_characters() -> None:
    node_id = new_node_id()
    assert short_id(node_id) == node_id[:8]
    assert short_id("p2") == "p2"  # shorter ids are shown whole
