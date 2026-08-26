import pytest

from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.scaling import discretize_wall_geometry
from brickhouse.building.models import Facade, OpeningType
from brickhouse.geometry.models import BuildingGeometry, OpeningGeometry, Point3D, WallGeometry


def _wall(facade: Facade, width: float, depth: float, height: float, openings=None) -> WallGeometry:
    if facade is Facade.FRONT:
        corners = [Point3D(x=0,y=0,z=0), Point3D(x=width,y=0,z=0), Point3D(x=width,y=0,z=height), Point3D(x=0,y=0,z=height)]
    elif facade is Facade.REAR:
        corners = [Point3D(x=width,y=depth,z=0), Point3D(x=0,y=depth,z=0), Point3D(x=0,y=depth,z=height), Point3D(x=width,y=depth,z=height)]
    elif facade is Facade.LEFT:
        corners = [Point3D(x=0,y=depth,z=0), Point3D(x=0,y=0,z=0), Point3D(x=0,y=0,z=height), Point3D(x=0,y=depth,z=height)]
    else:
        corners = [Point3D(x=width,y=0,z=0), Point3D(x=width,y=depth,z=0), Point3D(x=width,y=depth,z=height), Point3D(x=width,y=0,z=height)]
    return WallGeometry(id=f"vol:{facade.value}", volume_id="vol", facade=facade, corners=corners, openings=openings or [])


def test_opening_quality_separates_position_size_and_vertical_rounding():
    opening = OpeningGeometry(
        id="window",
        opening_type=OpeningType.WINDOW,
        volume_id="vol",
        facade=Facade.FRONT,
        corners=[
            Point3D(x=1.53,y=0,z=0.97), Point3D(x=2.76,y=0,z=0.97),
            Point3D(x=2.76,y=0,z=2.31), Point3D(x=1.53,y=0,z=2.31),
        ],
    )
    spec = discretize_wall_geometry(_wall(Facade.FRONT, 10, 8, 5.6, [opening]), 48)
    quality = spec.discretization_quality
    assert quality is not None
    by_quantity = {error.quantity: error for error in quality.errors if error.object_id == "window"}
    assert set(by_quantity) == {"opening_x", "opening_width", "opening_sill", "opening_height"}
    assert by_quantity["opening_x"].signed_error_units == pytest.approx(round(1.53 * 4.8) - 1.53 * 4.8)
    assert by_quantity["opening_width"].absolute_error_m > 0
    assert quality.worst_absolute_error_m == max(error.absolute_error_m for error in quality.errors)


def test_exact_grid_aligned_geometry_reports_zero_horizontal_error():
    opening = OpeningGeometry(
        id="door",
        opening_type=OpeningType.DOOR,
        volume_id="vol",
        facade=Facade.FRONT,
        corners=[
            Point3D(x=2,y=0,z=0), Point3D(x=4,y=0,z=0),
            Point3D(x=4,y=0,z=2.4), Point3D(x=2,y=0,z=2.4),
        ],
    )
    spec = discretize_wall_geometry(_wall(Facade.FRONT, 10, 8, 4.8, [opening]), 50)
    quality = spec.discretization_quality
    assert quality is not None
    horizontal = [e for e in quality.errors if e.quantity in {"wall_width", "opening_x", "opening_width"}]
    assert all(e.absolute_error_m == pytest.approx(0) for e in horizontal)


def test_building_shell_aggregates_four_facades_at_shared_scale():
    geometry = BuildingGeometry(
        building_id="house",
        walls=[
            _wall(Facade.FRONT, 10, 7.3, 5.6),
            _wall(Facade.REAR, 10, 7.3, 5.6),
            _wall(Facade.LEFT, 10, 7.3, 5.6),
            _wall(Facade.RIGHT, 10, 7.3, 5.6),
        ],
        roof_planes=[],
    )
    shell = generate_building_brick_shell(geometry, front_width_studs=48)
    quality = shell.discretization_quality
    assert quality is not None
    assert quality.studs_per_meter == pytest.approx(4.8)
    assert len(quality.walls) == 4
    all_errors = [error for wall in quality.walls for error in wall.errors]
    assert quality.mean_absolute_error_m == pytest.approx(sum(e.absolute_error_m for e in all_errors) / len(all_errors))
    assert quality.worst_wall_id in {wall.wall_id for wall in quality.walls}
