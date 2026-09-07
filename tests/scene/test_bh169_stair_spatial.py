import copy

import pytest

from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import (
    ArchitecturalScene,
    Platform,
    PropertyValue,
    SceneVolume,
    StairRun,
    analyze_stair_spatial,
)


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _value(value):
    return PropertyValue(value=value, source=SOURCE)


def _volume():
    return SceneVolume(
        id="host",
        position=Position3D(x=0, y=0, z=0),
        width=_value(6),
        depth=_value(6),
        height=_value(3),
        floors=1,
        source=SOURCE,
    )


def _platform():
    return Platform(
        id="landing",
        host_volume_id="host",
        position=Position3D(x=6, y=2, z=2.5),
        width=2,
        depth=2,
        thickness=0.2,
        source=SOURCE,
    )


def _stair(start, end, width=1.0):
    return StairRun(
        id="stair",
        start=Position3D(**start),
        end=Position3D(**end),
        width=width,
        source=SOURCE,
    )


def _scene(stair, *, volume=None, platform=None):
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh169-generic",
        name="Generic stair scene",
        volumes=[volume or _volume()],
        platforms=[] if platform is False else [platform or _platform()],
        stairs=[stair],
        appearance=Appearance(),
    )


def test_x_dominant_run_expands_only_by_half_width_perpendicular_to_centerline():
    stair = _stair(
        {"x": 0, "y": 1, "z": 0},
        {"x": 4, "y": 1, "z": 2},
        width=1.2,
    )
    corridor = analyze_stair_spatial(_scene(stair)).corridor("stair")
    assert corridor is not None and corridor.geometry_known is True
    assert corridor.x_min == pytest.approx(0)
    assert corridor.x_max == pytest.approx(4)
    assert corridor.y_min == pytest.approx(0.4)
    assert corridor.y_max == pytest.approx(1.6)
    assert corridor.z_min == pytest.approx(0)
    assert corridor.z_max == pytest.approx(2)
    assert corridor.horizontal_run == pytest.approx(4)
    assert corridor.solid_volume_known is False


def test_y_dominant_run_expands_in_x_by_half_width():
    stair = _stair(
        {"x": 2, "y": 0, "z": 0},
        {"x": 2, "y": 5, "z": 2.5},
        width=2,
    )
    corridor = analyze_stair_spatial(_scene(stair)).corridor("stair")
    assert corridor is not None
    assert corridor.x_min == pytest.approx(1)
    assert corridor.x_max == pytest.approx(3)
    assert corridor.y_min == pytest.approx(0)
    assert corridor.y_max == pytest.approx(5)


def test_diagonal_run_uses_true_perpendicular_corridor_not_axis_guess():
    stair = _stair(
        {"x": 0, "y": 0, "z": 0},
        {"x": 3, "y": 4, "z": 2},
        width=2,
    )
    corridor = analyze_stair_spatial(_scene(stair)).corridor("stair")
    assert corridor is not None
    assert corridor.horizontal_run == pytest.approx(5)
    assert corridor.x_min == pytest.approx(-0.8)
    assert corridor.x_max == pytest.approx(3.8)
    assert corridor.y_min == pytest.approx(-0.6)
    assert corridor.y_max == pytest.approx(4.6)


def test_degenerate_horizontal_run_stays_explicitly_unknown_without_invented_orientation():
    stair = _stair(
        {"x": 1, "y": 1, "z": 0},
        {"x": 1, "y": 1, "z": 2},
    )
    corridor = analyze_stair_spatial(_scene(stair)).corridor("stair")
    assert corridor is not None
    assert corridor.geometry_known is False
    assert corridor.x_min is None and corridor.y_min is None
    assert corridor.z_min == 0 and corridor.z_max == 2
    assert corridor.solid_volume_known is False


def test_endpoint_contact_detects_platform_top_without_claiming_solid_stair_body():
    stair = _stair(
        {"x": 4, "y": 3, "z": 0},
        {"x": 6.5, "y": 3, "z": 2.5},
    )
    report = analyze_stair_spatial(_scene(stair))
    contacts = report.contacts("stair", "end")
    assert [(item.target_id, item.contact_kind) for item in contacts] == [
        ("landing", "platform_top")
    ]


def test_endpoint_contact_detects_volume_boundary_and_rejects_noncontact():
    touching = _stair(
        {"x": 6, "y": 1, "z": 1},
        {"x": 8, "y": 1, "z": 2},
    )
    report = analyze_stair_spatial(_scene(touching, platform=False))
    assert [(item.target_id, item.contact_kind) for item in report.contacts("stair", "start")] == [
        ("host", "volume_boundary")
    ]

    away = _stair(
        {"x": 8, "y": 8, "z": 0},
        {"x": 10, "y": 8, "z": 2},
    )
    assert analyze_stair_spatial(_scene(away, platform=False)).contacts("stair") == []


def test_analysis_is_deterministic_and_non_mutating():
    stair = _stair(
        {"x": 0, "y": 0, "z": 0},
        {"x": 3, "y": 4, "z": 2},
        width=1.2,
    )
    scene = _scene(stair)
    before = copy.deepcopy(scene.model_dump(mode="json"))
    first = analyze_stair_spatial(scene).model_dump(mode="json")
    second = analyze_stair_spatial(scene).model_dump(mode="json")
    assert first == second
    assert scene.model_dump(mode="json") == before
