import pytest

from brickhouse.bricks.building_layout import BuildingBrickShell, BuildingWallLayout
from brickhouse.bricks.placement import generate_simple_wall_layout
from brickhouse.bricks.roof import create_m0_roof_catalog, generate_spatial_gable_roof
from brickhouse.bricks.scaling import WallGridSpec
from brickhouse.building.models import Facade, RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, Point3D, RoofPlaneGeometry


def _wall_record(facade, width, height=6):
    grid = WallGridSpec(
        wall_id=f"v:{facade.value}",
        width_studs=width,
        height_bricks=height,
        studs_per_meter=1.0,
        courses_per_meter=1.0,
        openings=[],
    )
    return BuildingWallLayout(
        wall_id=grid.wall_id,
        facade=facade,
        grid=grid,
        layout=generate_simple_wall_layout(width, height),
    )


def _shell(width=10, depth=8, height=6):
    return BuildingBrickShell(
        building_id="b",
        volume_id="v",
        reference_width_studs=width,
        studs_per_meter=1.0,
        walls=[
            _wall_record(Facade.FRONT, width, height),
            _wall_record(Facade.REAR, width, height),
            _wall_record(Facade.LEFT, depth, height),
            _wall_record(Facade.RIGHT, depth, height),
        ],
    )


def _geometry(ridge_direction):
    if ridge_direction is RidgeDirection.DEPTH:
        negative = [
            Point3D(x=0, y=0, z=6), Point3D(x=5, y=0, z=9),
            Point3D(x=5, y=8, z=9), Point3D(x=0, y=8, z=6),
        ]
        positive = [
            Point3D(x=5, y=0, z=9), Point3D(x=10, y=0, z=6),
            Point3D(x=10, y=8, z=6), Point3D(x=5, y=8, z=9),
        ]
    else:
        negative = [
            Point3D(x=0, y=0, z=6), Point3D(x=10, y=0, z=6),
            Point3D(x=10, y=4, z=9), Point3D(x=0, y=4, z=9),
        ]
        positive = [
            Point3D(x=0, y=4, z=9), Point3D(x=10, y=4, z=9),
            Point3D(x=10, y=8, z=6), Point3D(x=0, y=8, z=6),
        ]
    return BuildingGeometry(
        building_id="b",
        walls=[],
        roof_planes=[
            RoofPlaneGeometry(id="r:negative", roof_id="r", volume_id="v", roof_type=RoofType.GABLE, side="negative", ridge_direction=ridge_direction, corners=negative),
            RoofPlaneGeometry(id="r:positive", roof_id="r", volume_id="v", roof_type=RoofType.GABLE, side="positive", ridge_direction=ridge_direction, corners=positive),
        ],
    )


def test_roof_catalog_has_supplier_independent_tiles_and_ridge_parts():
    catalog = create_m0_roof_catalog()
    assert catalog.get("ROOF_TILE_1X8").category == "roof_tile"
    assert catalog.get("RIDGE_TILE_1X8").category == "ridge_tile"


@pytest.mark.parametrize("direction", [RidgeDirection.DEPTH, RidgeDirection.WIDTH])
def test_gable_roof_supports_both_ridge_directions(direction):
    roof = generate_spatial_gable_roof(_geometry(direction), _shell())
    assert roof.ridge_direction is direction
    assert any(p.side == "ridge" for p in roof.placements)
    assert all(p.z_plates >= 18 for p in roof.placements)


def test_two_planes_climb_toward_common_ridge():
    roof = generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), _shell())
    rows = {}
    for p in roof.placements:
        if p.side != "ridge":
            rows.setdefault(p.x_studs, p.z_plates)
    assert rows[0] == rows[9]
    assert rows[4] >= rows[1]
    ridge_z = max(p.z_plates for p in roof.placements if p.side == "ridge")
    assert ridge_z > max(rows.values())


def test_generated_roof_has_no_duplicate_occupied_cells():
    roof = generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), _shell())
    catalog = create_m0_roof_catalog()
    occupied = set()
    for p in roof.placements:
        part = catalog.get(p.part_id)
        fx, fy = (part.length_studs, part.width_studs) if p.rotation_quarter_turns % 2 else (part.width_studs, part.length_studs)
        cells = {(p.x_studs + dx, p.y_studs + dy, p.z_plates) for dx in range(fx) for dy in range(fy)}
        assert occupied.isdisjoint(cells)
        occupied.update(cells)


def test_generation_is_deterministic():
    first = generate_spatial_gable_roof(_geometry(RidgeDirection.WIDTH), _shell())
    second = generate_spatial_gable_roof(_geometry(RidgeDirection.WIDTH), _shell())
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_non_gable_or_missing_planes_are_rejected():
    geometry = BuildingGeometry(building_id="b", walls=[], roof_planes=[])
    with pytest.raises(ValueError, match="exactly two"):
        generate_spatial_gable_roof(geometry, _shell())
