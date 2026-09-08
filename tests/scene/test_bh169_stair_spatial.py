import copy

import pytest
from pydantic import ValidationError

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


def _volume(width=12, depth=12, height=4):
    return SceneVolume(
        id="host",
        position=Position3D(x=0, y=0, z=0),
        width=_value(width),
        depth=_value(depth),
        height=_value(height),
        floors=1,
        source=SOURCE,
    )


def _platform(x=6, y=2, z=2.5, width=2, depth=2):
    return Platform(
        id="landing",
        host_volume_id="host",
        position=Position3D(x=x, y=y, z=z),
        width=width,
        depth=depth,
        thickness=0.2,
        source=SOURCE,
    )


def _stair(start, end, width=1.0, stair_id="stair"):
    return StairRun(
        id=stair_id,
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


def _connected_scene_for(stair):
    """Give the test stair a real landing at its upper endpoint.

    Geometry tests must not bypass ArchitecturalScene connectivity merely to
    exercise the derived solver. The landing is placed so the endpoint is on
    its top surface and the platform also touches the host volume.
    """
    end = stair.end
    platform = _platform(x=end.x, y=end.y - 0.5, z=end.z, width=1.0, depth=1.0)
    volume = _volume(width=max(12, end.x + 1), depth=max(12, end.y + 1), height=max(4, end.z + 1))
    return _scene(stair, volume=volume, platform=platform)


def _multi_run_scene(*, turn_gap=0.0, straight=False):
    lower = _stair(
        {"x": 1, "y": 2, "z": 0},
        {"x": 3, "y": 2, "z": 1},
        stair_id="lower",
    )
    if straight:
        upper_start = {"x": 3 + turn_gap, "y": 2, "z": 1}
        upper_end = {"x": 8, "y": 2, "z": 2}
    else:
        upper_start = {"x": 3 + turn_gap, "y": 2, "z": 1}
        upper_end = {"x": 3, "y": 0, "z": 2}
    upper = _stair(upper_start, upper_end, stair_id="upper")
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh169-multi-run",
        name="Generic multi-run stair scene",
        volumes=[_volume(width=8, depth=8, height=4)],
        platforms=[],
        stairs=[upper, lower],
        appearance=Appearance(),
    )


def test_x_dominant_run_expands_only_by_half_width_perpendicular_to_centerline():
    stair = _stair({"x": 0, "y": 1, "z": 0}, {"x": 4, "y": 1, "z": 2}, width=1.2)
    corridor = analyze_stair_spatial(_connected_scene_for(stair)).corridor("stair")
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
    stair = _stair({"x": 2, "y": 0, "z": 0}, {"x": 2, "y": 5, "z": 2.5}, width=2)
    corridor = analyze_stair_spatial(_connected_scene_for(stair)).corridor("stair")
    assert corridor is not None
    assert corridor.x_min == pytest.approx(1)
    assert corridor.x_max == pytest.approx(3)
    assert corridor.y_min == pytest.approx(0)
    assert corridor.y_max == pytest.approx(5)


def test_diagonal_run_uses_true_perpendicular_corridor_not_axis_guess():
    stair = _stair({"x": 0, "y": 0, "z": 0}, {"x": 3, "y": 4, "z": 2}, width=2)
    corridor = analyze_stair_spatial(_connected_scene_for(stair)).corridor("stair")
    assert corridor is not None
    assert corridor.horizontal_run == pytest.approx(5)
    assert corridor.x_min == pytest.approx(-0.8)
    assert corridor.x_max == pytest.approx(3.8)
    assert corridor.y_min == pytest.approx(-0.6)
    assert corridor.y_max == pytest.approx(4.6)


def test_degenerate_horizontal_run_stays_explicitly_unknown_without_invented_orientation():
    stair = _stair({"x": 1, "y": 1, "z": 0}, {"x": 1, "y": 1, "z": 2})
    corridor = analyze_stair_spatial(_connected_scene_for(stair)).corridor("stair")
    assert corridor is not None
    assert corridor.geometry_known is False
    assert corridor.x_min is None and corridor.y_min is None
    assert corridor.z_min == 0 and corridor.z_max == 2
    assert corridor.solid_volume_known is False


def test_endpoint_contact_detects_platform_top_without_claiming_solid_stair_body():
    stair = _stair({"x": 4, "y": 3, "z": 0}, {"x": 6.5, "y": 3, "z": 2.5})
    report = analyze_stair_spatial(_scene(stair, volume=_volume(width=6), platform=_platform()))
    contacts = report.contacts("stair", "end")
    assert [(item.target_id, item.contact_kind) for item in contacts] == [("landing", "platform_top")]


def test_endpoint_contact_detects_volume_boundary():
    touching = _stair({"x": 0, "y": 1, "z": 0}, {"x": 6, "y": 1, "z": 2})
    report = analyze_stair_spatial(_scene(touching, volume=_volume(width=6), platform=False))
    assert [(item.target_id, item.contact_kind) for item in report.contacts("stair", "end")] == [
        ("host", "volume_boundary")
    ]


def test_analysis_does_not_report_contacts_that_are_not_geometrically_present():
    stair = _stair({"x": 0, "y": 1, "z": 0}, {"x": 4, "y": 1, "z": 2})
    scene = _connected_scene_for(stair)
    report = analyze_stair_spatial(scene)
    assert all(item.target_id != "host" for item in report.contacts("stair", "end"))


def test_multi_run_scene_accepts_direct_stair_junction_without_inventing_landing_geometry():
    scene = _multi_run_scene()
    assert scene.platforms == []

    report = analyze_stair_spatial(scene)
    assert len(report.run_junctions) == 1
    junction = report.run_junctions[0]
    assert (
        junction.first_stair_id,
        junction.first_endpoint,
        junction.second_stair_id,
        junction.second_endpoint,
    ) == ("lower", "end", "upper", "start")
    assert junction.changes_horizontal_direction is True


def test_collinear_connected_runs_are_not_mislabeled_as_a_turn():
    report = analyze_stair_spatial(_multi_run_scene(straight=True))
    assert len(report.run_junctions) == 1
    assert report.run_junctions[0].changes_horizontal_direction is False


def test_gap_outside_connectivity_tolerance_does_not_create_fake_stair_junction():
    with pytest.raises(ValidationError, match="does not connect"):
        _multi_run_scene(turn_gap=0.13)


def test_multi_run_analysis_is_deterministic_and_non_mutating():
    scene = _multi_run_scene()
    before = copy.deepcopy(scene.model_dump(mode="json"))
    first = analyze_stair_spatial(scene).model_dump(mode="json")
    second = analyze_stair_spatial(scene).model_dump(mode="json")
    assert first == second
    assert scene.model_dump(mode="json") == before


def test_analysis_is_deterministic_and_non_mutating():
    stair = _stair({"x": 0, "y": 0, "z": 0}, {"x": 3, "y": 4, "z": 2}, width=1.2)
    scene = _connected_scene_for(stair)
    before = copy.deepcopy(scene.model_dump(mode="json"))
    first = analyze_stair_spatial(scene).model_dump(mode="json")
    second = analyze_stair_spatial(scene).model_dump(mode="json")
    assert first == second
    assert scene.model_dump(mode="json") == before
