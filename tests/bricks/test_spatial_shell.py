from brickhouse.bricks import (
    BuildingBrickShell,
    BuildingWallLayout,
    WallGridSpec,
    WallOpeningGrid,
    generate_spatial_brick_shell,
    generate_wall_layout_with_openings,
)
from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.building.models import Facade


def _wall_record(facade, width, height, openings=None):
    openings = list(openings or [])
    grid = WallGridSpec(
        wall_id=f"vol:{facade.value}",
        width_studs=width,
        height_bricks=height,
        studs_per_meter=4.8,
        courses_per_meter=4.0,
        openings=openings,
    )
    return BuildingWallLayout(
        wall_id=grid.wall_id,
        facade=facade,
        grid=grid,
        layout=generate_wall_layout_with_openings(width, height, openings),
    )


def _shell(front_openings=None):
    return BuildingBrickShell(
        building_id="house",
        volume_id="vol",
        reference_width_studs=16,
        studs_per_meter=4.8,
        walls=[
            _wall_record(Facade.FRONT, 16, 6, front_openings),
            _wall_record(Facade.REAR, 16, 6),
            _wall_record(Facade.LEFT, 12, 6),
            _wall_record(Facade.RIGHT, 12, 6),
        ],
    )


def _occupied_by_placement(spatial):
    catalog = create_m0_brick_catalog()
    cells = []
    for placement in spatial.placements:
        width, depth = catalog.get(placement.brick_id).footprint(
            placement.rotation_quarter_turns
        )
        course = placement.z_plates // 3
        for dx in range(width):
            for dy in range(depth):
                cells.append(
                    (
                        placement.x_studs + dx,
                        placement.y_studs + dy,
                        course,
                        placement.facade,
                    )
                )
    return cells


def test_spatial_shell_dimensions_are_global():
    spatial = generate_spatial_brick_shell(_shell())
    assert spatial.width_studs == 16
    assert spatial.depth_studs == 12
    assert spatial.height_bricks == 6


def test_no_3d_grid_cell_is_occupied_twice():
    spatial = generate_spatial_brick_shell(_shell())
    cells = [(x, y, z) for x, y, z, _ in _occupied_by_placement(spatial)]
    assert len(cells) == len(set(cells))


def test_full_perimeter_is_covered_without_openings():
    spatial = generate_spatial_brick_shell(_shell())
    cells = {(x, y, z) for x, y, z, _ in _occupied_by_placement(spatial)}
    expected = {
        (x, y, z)
        for z in range(6)
        for x in range(16)
        for y in range(12)
        if x in {0, 15} or y in {0, 11}
    }
    assert cells == expected


def test_corner_ownership_alternates_by_course():
    spatial = generate_spatial_brick_shell(_shell())
    by_cell = {
        (x, y, z): facade
        for x, y, z, facade in _occupied_by_placement(spatial)
    }
    assert by_cell[(0, 0, 0)] is Facade.FRONT
    assert by_cell[(15, 0, 0)] is Facade.FRONT
    assert by_cell[(0, 0, 1)] is Facade.LEFT
    assert by_cell[(15, 0, 1)] is Facade.RIGHT


def test_front_opening_remains_empty_in_global_shell():
    opening = WallOpeningGrid(
        id="door",
        x_studs=6,
        z_bricks=0,
        width_studs=4,
        height_bricks=3,
    )
    spatial = generate_spatial_brick_shell(_shell([opening]))
    cells = {(x, y, z) for x, y, z, _ in _occupied_by_placement(spatial)}
    for z in range(3):
        for x in range(6, 10):
            assert (x, 0, z) not in cells


def test_front_and_rear_run_on_x_axis_and_sides_on_y_axis():
    spatial = generate_spatial_brick_shell(_shell())
    catalog = create_m0_brick_catalog()
    for placement in spatial.placements:
        width, depth = catalog.get(placement.brick_id).footprint(
            placement.rotation_quarter_turns
        )
        if placement.facade in {Facade.FRONT, Facade.REAR}:
            assert depth == 1
        else:
            assert width == 1


def test_generation_is_deterministic():
    first = generate_spatial_brick_shell(_shell())
    second = generate_spatial_brick_shell(_shell())
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
