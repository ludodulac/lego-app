from types import SimpleNamespace

from brickhouse.scene.topology_fidelity import _relation_endpoints_match
from brickhouse.survey import RelationKind


def _relation(kind, subject_id, object_id, *, anchor=None):
    return SimpleNamespace(
        kind=kind,
        subject_id=subject_id,
        object_id=object_id,
        semantic_anchor_volume_id=anchor,
    )


def test_anchored_building_boundary_alias_preserves_survey_boundary_identity():
    survey = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "obs-building-boundary-left")
    scene = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "building_boundary", anchor="volume_main")

    assert _relation_endpoints_match(
        survey,
        scene,
        building_boundary_ids={"obs-building-boundary-left"},
    )


def test_anchored_boundary_alias_also_works_with_reversed_symmetric_endpoints():
    survey = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "obs-building-boundary-left")
    scene = _relation(RelationKind.CONNECTS_TO, "building_boundary", "obs-left-platform", anchor="volume_main")

    assert _relation_endpoints_match(
        survey,
        scene,
        building_boundary_ids={"obs-building-boundary-left"},
    )


def test_unanchored_building_boundary_alias_is_rejected():
    survey = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "obs-building-boundary-left")
    scene = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "building_boundary")

    assert not _relation_endpoints_match(
        survey,
        scene,
        building_boundary_ids={"obs-building-boundary-left"},
    )


def test_alias_cannot_replace_non_boundary_survey_object():
    survey = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "obs-left-stair")
    scene = _relation(RelationKind.CONNECTS_TO, "obs-left-platform", "building_boundary", anchor="volume_main")

    assert not _relation_endpoints_match(
        survey,
        scene,
        building_boundary_ids={"obs-building-boundary-left"},
    )
