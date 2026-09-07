import pytest

from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, Platform, PropertyValue, SceneVolume
from brickhouse.scene.spatial_analysis import analyze_scene_spatial_relations


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _value(value):
    return PropertyValue(value=value, source=SOURCE)


def _volume(object_id, *, x, y, z, width, depth, height):
    return SceneVolume(
        id=object_id,
        position=Position3D(x=x, y=y, z=z),
        width=_value(width),
        depth=_value(depth),
        height=_value(height),
        floors=1,
        source=SOURCE,
    )


def _scene(*volumes, platforms=None):
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh164-generic",
        name="Generic spatial scene",
        volumes=list(volumes),
        platforms=list(platforms or []),
        appearance=Appearance(),
    )


def test_canonical_directionality_uses_x_left_right_y_front_rear_and_z_bottom_top():
    front_low = _volume(
        "front-low", x=0, y=0, z=0, width=2, depth=2, height=2
    )
    rear_high = _volume(
        "rear-high", x=0, y=3, z=3, width=2, depth=2, height=2
    )
    report = analyze_scene_spatial_relations(_scene(front_low, rear_high))

    forward = report.relation("front-low", "rear-high")
    reverse = report.relation("rear-high", "front-low")
    assert forward is not None and reverse is not None
    assert forward.front_of is True
    assert forward.behind is False
    assert forward.below is True
    assert forward.above is False
    assert reverse.behind is True
    assert reverse.above is True
    assert forward.y_gap == reverse.y_gap == 1
    assert forward.z_gap == reverse.z_gap == 1


def test_overlap_and_face_adjacency_are_distinct_geometric_facts():
    base = _volume("base", x=0, y=0, z=0, width=2, depth=2, height=2)
    adjacent = _volume(
        "adjacent", x=2.05, y=0, z=0, width=2, depth=2, height=2
    )
    overlapping = _volume(
        "overlap", x=1, y=1, z=1, width=2, depth=2, height=2
    )
    report = analyze_scene_spatial_relations(_scene(base, adjacent, overlapping))

    touching = report.relation("base", "adjacent")
    overlap = report.relation("base", "overlap")
    assert touching is not None and overlap is not None
    assert touching.adjacent_face is True
    assert touching.overlaps_3d is False
    assert touching.x_gap == pytest.approx(0.05)
    assert overlap.overlaps_xy is True
    assert overlap.overlaps_3d is True
    assert overlap.adjacent_face is False
    assert overlap.x_overlap == pytest.approx(1)
    assert overlap.y_overlap == pytest.approx(1)
    assert overlap.z_overlap == pytest.approx(1)


def test_containment_is_directional_and_reverse_pair_is_consistent():
    outer = _volume("outer", x=0, y=0, z=0, width=4, depth=4, height=4)
    inner = _volume("inner", x=1, y=1, z=1, width=1, depth=1, height=1)
    report = analyze_scene_spatial_relations(_scene(outer, inner))

    outward = report.relation("outer", "inner")
    inward = report.relation("inner", "outer")
    assert outward is not None and inward is not None
    assert outward.contains_object is True
    assert outward.contained_by_object is False
    assert inward.contains_object is False
    assert inward.contained_by_object is True
    assert outward.overlaps_3d is inward.overlaps_3d is True


def test_platform_envelope_uses_slab_thickness_below_walkable_level():
    host = _volume("host", x=0, y=0, z=0, width=4, depth=4, height=3)
    platform = Platform(
        id="deck",
        host_volume_id="host",
        position=Position3D(x=4, y=1, z=2),
        width=2,
        depth=2,
        thickness=0.2,
        source=SOURCE,
    )
    report = analyze_scene_spatial_relations(_scene(host, platforms=[platform]))
    deck = next(item for item in report.envelopes if item.object_id == "deck")
    relation = report.relation("deck", "host")

    assert deck.geometry_known is True
    assert deck.z_min == pytest.approx(1.8)
    assert deck.z_max == pytest.approx(2)
    assert relation is not None
    assert relation.adjacent_face is True
    assert relation.x_gap == pytest.approx(0)
    assert relation.x_overlap == pytest.approx(0)
    assert relation.y_overlap == pytest.approx(2)
    assert relation.z_overlap == pytest.approx(0.2)


def test_incomplete_volume_geometry_stays_explicitly_unknown():
    incomplete = _volume(
        "unknown-width", x=0, y=0, z=0, width=None, depth=2, height=2
    )
    complete = _volume("complete", x=3, y=0, z=0, width=2, depth=2, height=2)
    report = analyze_scene_spatial_relations(_scene(incomplete, complete))

    envelope = next(item for item in report.envelopes if item.object_id == "unknown-width")
    relation = report.relation("unknown-width", "complete")
    assert envelope.geometry_known is False
    assert envelope.x_min is None
    assert relation is not None
    assert relation.geometry_known is False
    assert relation.left_of is None
    assert relation.overlaps_3d is None
    assert relation.x_gap is None


def test_report_order_and_pair_facts_are_deterministic_independent_of_scene_input_order():
    first = _volume("a", x=0, y=0, z=0, width=2, depth=2, height=2)
    second = _volume("b", x=3, y=0, z=0, width=2, depth=2, height=2)

    one = analyze_scene_spatial_relations(_scene(first, second)).model_dump()
    two = analyze_scene_spatial_relations(_scene(second, first)).model_dump()

    assert one == two
    assert [item["object_id"] for item in one["envelopes"]] == ["a", "b"]
    assert [(item["subject_id"], item["object_id"]) for item in one["pairs"]] == [
        ("a", "b"),
        ("b", "a"),
    ]
