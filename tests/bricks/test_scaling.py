import pytest

from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.scaling import (
    COURSES_PER_STUD_RATIO,
    discretize_wall_geometry,
    generate_scaled_wall_layout,
)
from brickhouse.building.models import Facade, OpeningType
from brickhouse.geometry.models import OpeningGeometry, Point3D, WallGeometry


def _front_wall(width=10.0, height=5.6, openings=None):
    return WallGeometry(
        id="vol:front",
        volume_id="vol",
        facade=Facade.FRONT,
        corners=[
            Point3D(x=0, y=0, z=0),
            Point3D(x=width, y=0, z=0),
            Point3D(x=width, y=0, z=height),
            Point3D(x=0, y=0, z=height),
        ],
        openings=openings or [],
    )


def _opening(opening_id, x0, x1, z0, z1, facade=Facade.FRONT):
    return OpeningGeometry(
        id=opening_id,
        opening_type=OpeningType.WINDOW,
        volume_id="vol",
        facade=facade,
        corners=[
            Point3D(x=x0, y=0, z=z0),
            Point3D(x=x1, y=0, z=z0),
            Point3D(x=x1, y=0, z=z1),
            Point3D(x=x0, y=0, z=z1),
        ],
    )


def test_10m_wall_to_50_studs_uses_coherent_scale():
    spec = discretize_wall_geometry(_front_wall(width=10, height=6), 50)
    assert spec.width_studs == 50
    assert spec.studs_per_meter == pytest.approx(5.0)
    assert spec.courses_per_meter == pytest.approx(5.0 * COURSES_PER_STUD_RATIO)
    assert spec.height_bricks == 25


def test_rounding_is_half_up_and_deterministic():
    spec = discretize_wall_geometry(_front_wall(width=10, height=5.6), 48)
    assert spec.width_studs == 48
    assert spec.height_bricks == 22
    again = discretize_wall_geometry(_front_wall(width=10, height=5.6), 48)
    assert spec.model_dump(mode="json") == again.model_dump(mode="json")


def test_door_maps_to_grid_and_starts_at_ground():
    door = _opening("door", 4.5, 5.5, 0.0, 2.1)
    wall = _front_wall(openings=[door])
    spec = discretize_wall_geometry(wall, 50)
    grid = spec.openings[0]
    assert grid.x_studs == 23
    assert grid.width_studs == 5
    assert grid.z_bricks == 0
    assert grid.height_bricks == 9


def test_floating_window_maps_position_and_size():
    window = _opening("window", 1.5, 2.7, 1.0, 2.3)
    spec = discretize_wall_geometry(_front_wall(openings=[window]), 50)
    grid = spec.openings[0]
    assert grid.x_studs == 8
    assert grid.width_studs == 6
    assert grid.z_bricks == 4
    assert grid.height_bricks == 6


def test_reversed_wall_axis_still_uses_local_opening_position():
    wall = WallGeometry(
        id="vol:rear",
        volume_id="vol",
        facade=Facade.REAR,
        corners=[
            Point3D(x=10, y=8, z=0),
            Point3D(x=0, y=8, z=0),
            Point3D(x=0, y=8, z=5),
            Point3D(x=10, y=8, z=5),
        ],
        openings=[
            OpeningGeometry(
                id="rear_window",
                opening_type=OpeningType.WINDOW,
                volume_id="vol",
                facade=Facade.REAR,
                corners=[
                    Point3D(x=8, y=8, z=1),
                    Point3D(x=6, y=8, z=1),
                    Point3D(x=6, y=8, z=2),
                    Point3D(x=8, y=8, z=2),
                ],
            )
        ],
    )
    grid = discretize_wall_geometry(wall, 50).openings[0]
    assert grid.x_studs == 10
    assert grid.width_studs == 10


def test_side_wall_orientation_is_independent_of_world_axis():
    wall = WallGeometry(
        id="vol:right",
        volume_id="vol",
        facade=Facade.RIGHT,
        corners=[
            Point3D(x=10, y=0, z=0),
            Point3D(x=10, y=8, z=0),
            Point3D(x=10, y=8, z=4),
            Point3D(x=10, y=0, z=4),
        ],
        openings=[
            OpeningGeometry(
                id="side_window",
                opening_type=OpeningType.WINDOW,
                volume_id="vol",
                facade=Facade.RIGHT,
                corners=[
                    Point3D(x=10, y=2, z=1),
                    Point3D(x=10, y=4, z=1),
                    Point3D(x=10, y=4, z=2),
                    Point3D(x=10, y=2, z=2),
                ],
            )
        ],
    )
    spec = discretize_wall_geometry(wall, 40)
    assert spec.studs_per_meter == pytest.approx(5)
    assert spec.openings[0].x_studs == 10
    assert spec.openings[0].width_studs == 10


def test_tiny_feature_that_collapses_is_rejected():
    tiny = _opening("tiny", 1.0, 1.01, 1.0, 1.01)
    with pytest.raises(ValueError, match="collapses"):
        discretize_wall_geometry(_front_wall(openings=[tiny]), 20)


@pytest.mark.parametrize("target", [0, -1, -50])
def test_invalid_target_width_is_rejected(target):
    with pytest.raises(ValueError):
        discretize_wall_geometry(_front_wall(), target)


def test_multiple_openings_preserve_order_and_remain_disjoint():
    first = _opening("first", 1.0, 2.0, 1.0, 2.0)
    second = _opening("second", 3.0, 4.0, 1.0, 2.0)
    spec = discretize_wall_geometry(_front_wall(openings=[first, second]), 50)
    assert [opening.id for opening in spec.openings] == ["first", "second"]
    assert spec.openings[0].x_end <= spec.openings[1].x_studs


def test_scaled_layout_keeps_opening_cells_empty():
    door = _opening("door", 4.0, 6.0, 0.0, 2.4)
    wall = _front_wall(width=10, height=5, openings=[door])
    layout = generate_scaled_wall_layout(wall, 40)
    opening = layout.openings[0]
    catalog = create_m0_brick_catalog()

    assert layout.wall_width_studs == 40
    assert opening.x_studs == 16
    assert opening.width_studs == 8

    for placement in layout.placements:
        course = placement.z_plates // 3
        brick = catalog.get(placement.brick_id)
        span, depth = brick.footprint(placement.rotation_quarter_turns)
        assert depth == 1
        if opening.z_bricks <= course < opening.z_end:
            assert not (
                placement.x_studs < opening.x_end
                and opening.x_studs < placement.x_studs + span
            )
