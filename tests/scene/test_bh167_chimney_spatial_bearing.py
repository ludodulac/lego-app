import copy

from brickhouse.building import Appearance, Position3D, RidgeDirection, SourceInfo, SourceKind
from brickhouse.scene import (
    ArchitecturalScene,
    Chimney,
    PropertyValue,
    SceneRoof,
    SceneRoofType,
    SceneVolume,
)
from brickhouse.scene.spatial_analysis import analyze_scene_spatial_relations


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _value(value):
    return PropertyValue(value=value, source=SOURCE)


def _volume(*, width=6.0, depth=8.0, height=6.0):
    return SceneVolume(
        id="house",
        position=Position3D(x=0, y=0, z=0),
        width=_value(width),
        depth=_value(depth),
        height=_value(height),
        floors=2,
        source=SOURCE,
    )


def _chimney(*, x=1.0, y=2.0, z=6.0):
    return Chimney(
        id="chimney",
        position=Position3D(x=x, y=y, z=z),
        width=1.0,
        depth=1.0,
        height=2.0,
        source=SOURCE,
    )


def _scene(*, volume=None, chimney=None, roofs=None):
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh167-generic",
        name="Generic chimney scene",
        volumes=[volume or _volume()],
        chimneys=[chimney or _chimney()],
        roofs=list(roofs or []),
        appearance=Appearance(),
    )


def test_chimney_has_exact_scene_occupancy_envelope():
    report = analyze_scene_spatial_relations(_scene())
    envelope = next(item for item in report.envelopes if item.object_id == "chimney")

    assert envelope.object_kind == "chimney"
    assert envelope.geometry_known is True
    assert envelope.x_min == 1.0
    assert envelope.x_max == 2.0
    assert envelope.y_min == 2.0
    assert envelope.y_max == 3.0
    assert envelope.z_min == 6.0
    assert envelope.z_max == 8.0


def test_chimney_at_host_wall_top_has_explicit_volume_contact():
    report = analyze_scene_spatial_relations(_scene())
    bearing = report.chimney_support("chimney")

    assert bearing is not None
    assert bearing.status == "volume_contact"
    assert bearing.supporting_volume_ids == ["house"]
    assert bearing.roof_volume_ids_requiring_plane == []


def test_chimney_embedded_into_host_volume_is_contact_not_floating():
    report = analyze_scene_spatial_relations(_scene(chimney=_chimney(z=5.5)))
    bearing = report.chimney_support("chimney")

    assert bearing is not None
    assert bearing.status == "volume_contact"
    assert bearing.supporting_volume_ids == ["house"]


def test_chimney_above_pitched_host_requires_real_roof_plane_instead_of_box_contact():
    roof = SceneRoof(
        id="roof",
        volume_id="house",
        type=SceneRoofType.GABLE,
        overhang=0.2,
        ridge_direction=RidgeDirection.DEPTH,
        pitch_degrees=30,
        source=SOURCE,
    )
    report = analyze_scene_spatial_relations(
        _scene(chimney=_chimney(z=7.0), roofs=[roof])
    )
    bearing = report.chimney_support("chimney")

    assert bearing is not None
    assert bearing.status == "roof_plane_required"
    assert bearing.supporting_volume_ids == []
    assert bearing.roof_volume_ids_requiring_plane == ["house"]


def test_chimney_above_flat_host_without_contact_is_unsupported():
    roof = SceneRoof(
        id="roof",
        volume_id="house",
        type=SceneRoofType.FLAT,
        overhang=0.0,
        source=SOURCE,
    )
    report = analyze_scene_spatial_relations(
        _scene(chimney=_chimney(z=7.0), roofs=[roof])
    )
    bearing = report.chimney_support("chimney")

    assert bearing is not None
    assert bearing.status == "unsupported"


def test_chimney_outside_host_xy_footprint_is_unsupported():
    report = analyze_scene_spatial_relations(_scene(chimney=_chimney(x=10.0)))
    bearing = report.chimney_support("chimney")

    assert bearing is not None
    assert bearing.status == "unsupported"


def test_incomplete_host_geometry_does_not_create_fake_chimney_support():
    report = analyze_scene_spatial_relations(
        _scene(volume=_volume(width=None))
    )
    bearing = report.chimney_support("chimney")

    assert bearing is not None
    assert bearing.status == "unknown_host_geometry"
    assert bearing.supporting_volume_ids == []


def test_chimney_spatial_analysis_is_deterministic_and_non_mutating():
    scene = _scene()
    before = copy.deepcopy(scene.model_dump(mode="json"))

    first = analyze_scene_spatial_relations(scene).model_dump(mode="json")
    second = analyze_scene_spatial_relations(scene).model_dump(mode="json")

    assert first == second
    assert scene.model_dump(mode="json") == before
