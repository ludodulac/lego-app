from types import SimpleNamespace

from brickhouse.scene.topology_fidelity import _relation_endpoints_match
from brickhouse.survey import RelationKind


def _relation(kind, subject_id, object_id):
    return SimpleNamespace(kind=kind, subject_id=subject_id, object_id=object_id)


def test_reversed_connects_to_preserves_same_undirected_fact():
    survey = _relation(RelationKind.CONNECTS_TO, "platform", "building_boundary")
    scene = _relation(RelationKind.CONNECTS_TO, "building_boundary", "platform")

    assert _relation_endpoints_match(survey, scene)


def test_reversed_adjacent_to_preserves_same_undirected_fact():
    survey = _relation(RelationKind.ADJACENT_TO, "terrace", "landing")
    scene = _relation(RelationKind.ADJACENT_TO, "landing", "terrace")

    assert _relation_endpoints_match(survey, scene)


def test_reversed_supports_remains_directional_and_is_rejected():
    survey = _relation(RelationKind.SUPPORTS, "post", "platform")
    scene = _relation(RelationKind.SUPPORTS, "platform", "post")

    assert not _relation_endpoints_match(survey, scene)


def test_reversed_part_of_remains_directional_and_is_rejected():
    survey = _relation(RelationKind.PART_OF, "landing", "terrace")
    scene = _relation(RelationKind.PART_OF, "terrace", "landing")

    assert not _relation_endpoints_match(survey, scene)
