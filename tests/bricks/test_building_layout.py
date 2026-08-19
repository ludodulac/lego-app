import pytest

from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.building.models import Facade, OpeningType
from brickhouse.geometry.models import BuildingGeometry, OpeningGeometry, Point3D, WallGeometry


def _wall(facade, width, height=5.6, opening=None):
    if facade is Facade.FRONT:
        corners = [Point3D(x=0,y=0,z=0), Point3D(x=width,y=0,z=0), Point3D(x=width,y=0,z=height), Point3D(x=0,y=0,z=height)]
    elif facade is Facade.REAR:
        corners = [Point3D(x=width,y=8,z=0), Point3D(x=0,y=8,z=0), Point3D(x=0,y=8,z=height), Point3D(x=width,y=8,z=height)]
    elif facade is Facade.LEFT:
        corners = [Point3D(x=0,y=width,z=0), Point3D(x=0,y=0,z=0), Point3D(x=0,y=0,z=height), Point3D(x=0,y=width,z=height)]
    else:
        corners = [Point3D(x=10,y=0,z=0), Point3D(x=10,y=width,z=0), Point3D(x=10,y=width,z=height), Point3D(x=10,y=0,z=height)]
    return WallGeometry(id=f"vol:{facade.value}", volume_id="vol", facade=facade, corners=corners, openings=[opening] if opening else [])


def _front_opening():
    return OpeningGeometry(
        id="door",
        opening_type=OpeningType.DOOR,
        volume_id="vol",
        facade=Facade.FRONT,
        corners=[Point3D(x=4,y=0,z=0), Point3D(x=6,y=0,z=0), Point3D(x=6,y=0,z=2.4), Point3D(x=4,y=0,z=2.4)],
    )


def _geometry(front_opening=None):
    return BuildingGeometry(
        building_id="house",
        walls=[
            _wall(Facade.FRONT, 10, opening=front_opening),
            _wall(Facade.REAR, 10),
            _wall(Facade.LEFT, 8),
            _wall(Facade.RIGHT, 8),
        ],
        roof_planes=[],
    )


def test_10_by_8_house_uses_one_shared_scale():
    shell = generate_building_brick_shell(_geometry(), 48)
    widths = {record.facade: record.grid.width_studs for record in shell.walls}
    assert widths[Facade.FRONT] == 48
    assert widths[Facade.REAR] == 48
    assert widths[Facade.LEFT] == 38
    assert widths[Facade.RIGHT] == 38
    assert shell.studs_per_meter == pytest.approx(4.8)


def test_all_four_walls_share_one_height():
    shell = generate_building_brick_shell(_geometry(), 48)
    assert {record.grid.height_bricks for record in shell.walls} == {22}


def test_front_opening_is_scaled_and_kept_empty():
    shell = generate_building_brick_shell(_geometry(_front_opening()), 48)
    front = next(record for record in shell.walls if record.facade is Facade.FRONT)
    assert len(front.grid.openings) == 1
    opening = front.grid.openings[0]
    assert opening.x_studs == 19
    assert opening.width_studs == 10
    for placement in front.layout.placements:
        course = placement.z_plates // 3
        if opening.z_bricks <= course < opening.z_end:
            assert not (opening.x_studs <= placement.x_studs < opening.x_end)


def test_output_is_deterministic():
    first = generate_building_brick_shell(_geometry(_front_opening()), 48)
    second = generate_building_brick_shell(_geometry(_front_opening()), 48)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_missing_wall_is_rejected():
    geometry = _geometry()
    geometry.walls = geometry.walls[:-1]
    with pytest.raises(ValueError, match="exactly four walls"):
        generate_building_brick_shell(geometry, 48)


def test_multiple_volume_ids_are_rejected():
    geometry = _geometry()
    geometry.walls[-1].volume_id = "other"
    with pytest.raises(ValueError, match="one volume"):
        generate_building_brick_shell(geometry, 48)


def test_duplicate_facade_is_rejected():
    geometry = _geometry()
    geometry.walls[-1].facade = Facade.FRONT
    with pytest.raises(ValueError, match="duplicate wall"):
        generate_building_brick_shell(geometry, 48)


@pytest.mark.parametrize("target", [0, -1])
def test_invalid_reference_width_is_rejected(target):
    with pytest.raises(ValueError):
        generate_building_brick_shell(_geometry(), target)
