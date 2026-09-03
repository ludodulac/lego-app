from types import SimpleNamespace

from brickhouse.bricks.scene_architecture import (
    _connected_platform_course,
    _course_z,
    _stair_parts,
)
from brickhouse.scene.models import ExteriorMaterial


def _position(x, y, z):
    return SimpleNamespace(x=x, y=y, z=z)


def _scene_with_platform(*, platform_z=0.44):
    source = SimpleNamespace()
    volume = SimpleNamespace(
        id="main",
        position=_position(0.0, 0.0, 0.0),
        width=SimpleNamespace(value=10.0),
        depth=SimpleNamespace(value=8.0),
        height=SimpleNamespace(value=6.0),
    )
    platform = SimpleNamespace(
        id="landing",
        position=_position(4.0, 0.0, platform_z),
        width=2.0,
        depth=2.0,
        thickness=0.2,
        supports=[],
        material=ExteriorMaterial.MASONRY,
        deck_board_direction=None,
        edge_treatment=None,
        edges=None,
        host_volume_id="main",
        evidence=[],
        source=source,
    )
    return SimpleNamespace(
        volumes=[volume],
        platforms=[platform],
        stairs=[],
        terrain=None,
        notes=None,
    )


def test_connected_endpoint_uses_platform_course_when_independent_rounding_disagrees():
    scene = _scene_with_platform(platform_z=0.44)
    endpoint = _position(4.0, 1.0, 0.46)

    independent = _course_z(endpoint.z, 0.0, 10.0)
    platform_course = _course_z(scene.platforms[0].position.z, 0.0, 10.0)
    connected = _connected_platform_course(
        endpoint,
        scene,
        origin_z=0.0,
        plates_per_meter=10.0,
    )

    assert independent == 6
    assert platform_course == 3
    assert connected == platform_course


def test_stair_generation_keeps_terminal_tread_and_masonry_body_on_shared_level():
    scene = _scene_with_platform(platform_z=0.44)
    stair = SimpleNamespace(
        id="access",
        start=_position(0.0, 1.0, 0.0),
        end=_position(4.0, 1.0, 0.46),
        width=1.0,
        material=ExteriorMaterial.MASONRY,
        left_edge=None,
        right_edge=None,
        evidence=[],
    )
    source_end = stair.end.z

    parts = _stair_parts(
        stair,
        scene,
        origin_x=0.0,
        origin_y=0.0,
        origin_z=0.0,
        studs_per_meter=1.0,
        plates_per_meter=10.0,
    )

    terminal_treads = [
        part
        for part in parts
        if part.placement_id.startswith("scene-stair:access:tread:")
        and part.x_studs == 4
    ]
    terminal_body = [
        part
        for part in parts
        if part.placement_id.startswith("scene-stair:access:body:")
        and part.x_studs == 4
    ]

    assert stair.end.z == source_end
    assert {part.z_plates for part in terminal_treads} == {3}
    assert {part.z_plates for part in terminal_body} == {0}
    assert all(part.placement_id.startswith("scene-stair:access:") for part in parts)


def test_endpoint_outside_scene_connectivity_tolerance_keeps_own_course():
    scene = _scene_with_platform(platform_z=0.30)
    endpoint = _position(4.0, 1.0, 0.46)

    assert _connected_platform_course(
        endpoint,
        scene,
        origin_z=0.0,
        plates_per_meter=10.0,
    ) is None
    assert _course_z(endpoint.z, 0.0, 10.0) == 6
