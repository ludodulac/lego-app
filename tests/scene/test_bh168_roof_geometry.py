import copy

import pytest

from brickhouse.building import Appearance, Position3D, RidgeDirection, SourceInfo, SourceKind
from brickhouse.scene import (
    ArchitecturalScene,
    PropertyValue,
    RoofPitchRange,
    SceneRoof,
    SceneRoofType,
    SceneVolume,
    derive_roof_geometry,
    derive_scene_roof_geometry,
)


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _value(value):
    return PropertyValue(value=value, source=SOURCE)


def _volume(*, width=8.0, depth=6.0, height=4.0):
    return SceneVolume(
        id="house",
        position=Position3D(x=10.0, y=20.0, z=2.0),
        width=_value(width),
        depth=_value(depth),
        height=_value(height),
        floors=2,
        source=SOURCE,
    )


def _roof(*, ridge=RidgeDirection.DEPTH, pitch=45.0, overhang=1.0, pitch_range=None):
    return SceneRoof(
        id="roof",
        volume_id="house",
        type=SceneRoofType.GABLE,
        overhang=overhang,
        ridge_direction=ridge,
        pitch_degrees=pitch,
        pitch_range_degrees=pitch_range,
        source=SOURCE,
    )


def _scene(volume, roof):
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh168-generic",
        name="Generic roof scene",
        volumes=[volume],
        roofs=[roof],
        appearance=Appearance(),
    )


def test_depth_ridge_derives_x_slopes_wall_support_lines_and_outer_eaves():
    assessment = derive_roof_geometry(_roof(), _volume())
    assert assessment.status == "exact_gable"
    geometry = assessment.geometry
    assert geometry is not None

    assert geometry.slope_axis == "x"
    assert geometry.wall_top_z == pytest.approx(6.0)
    assert geometry.ridge.fixed_coordinate == pytest.approx(14.0)
    assert geometry.ridge_z == pytest.approx(10.0)
    assert geometry.ridge.span_min == pytest.approx(19.0)
    assert geometry.ridge.span_max == pytest.approx(27.0)

    assert [line.fixed_coordinate for line in geometry.support_lines] == pytest.approx([10.0, 18.0])
    assert [line.z for line in geometry.support_lines] == pytest.approx([6.0, 6.0])
    assert [line.fixed_coordinate for line in geometry.eaves] == pytest.approx([9.0, 19.0])
    assert [line.z for line in geometry.eaves] == pytest.approx([5.0, 5.0])


def test_width_ridge_derives_y_slopes_and_correct_ridge_height():
    assessment = derive_roof_geometry(
        _roof(ridge=RidgeDirection.WIDTH, pitch=45.0, overhang=0.0),
        _volume(),
    )
    geometry = assessment.geometry
    assert geometry is not None
    assert geometry.slope_axis == "y"
    assert geometry.ridge.fixed_coordinate == pytest.approx(23.0)
    assert geometry.ridge_z == pytest.approx(9.0)
    assert [line.fixed_coordinate for line in geometry.support_lines] == pytest.approx([20.0, 26.0])


def test_plane_z_query_hits_ridge_wall_support_and_outer_eave_consistently():
    geometry = derive_roof_geometry(_roof(), _volume()).geometry
    assert geometry is not None

    assert geometry.z_at(14.0, 23.0) == pytest.approx(10.0)
    assert geometry.z_at(10.0, 23.0) == pytest.approx(6.0)
    assert geometry.z_at(18.0, 23.0) == pytest.approx(6.0)
    assert geometry.z_at(9.0, 23.0) == pytest.approx(5.0)
    assert geometry.z_at(19.0, 23.0) == pytest.approx(5.0)
    assert geometry.z_at(8.9, 23.0) is None


def test_pitch_range_is_not_silently_collapsed_to_a_construction_angle():
    pitch_range = RoofPitchRange(
        min_degrees=25.0,
        max_degrees=35.0,
        source=SOURCE,
    )
    roof = _roof(pitch=None, pitch_range=pitch_range)
    assessment = derive_roof_geometry(roof, _volume())
    assert assessment.status == "missing_exact_pitch"
    assert assessment.geometry is None


def test_incomplete_host_geometry_remains_unknown():
    assessment = derive_roof_geometry(_roof(), _volume(width=None))
    assert assessment.status == "unknown_host_geometry"
    assert assessment.geometry is None


def test_non_gable_roof_is_not_forced_into_gable_planes():
    roof = SceneRoof(
        id="roof",
        volume_id="house",
        type=SceneRoofType.FLAT,
        overhang=0.2,
        source=SOURCE,
    )
    assessment = derive_roof_geometry(roof, _volume())
    assert assessment.status == "unsupported_roof_type"
    assert assessment.geometry is None


def test_scene_roof_geometry_is_deterministic_and_non_mutating():
    scene = _scene(_volume(), _roof())
    before = copy.deepcopy(scene.model_dump(mode="json"))

    first = [item.model_dump(mode="json") for item in derive_scene_roof_geometry(scene)]
    second = [item.model_dump(mode="json") for item in derive_scene_roof_geometry(scene)]

    assert first == second
    assert scene.model_dump(mode="json") == before
