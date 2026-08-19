import pytest
from pydantic import ValidationError

from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.placement import (
    WallOpeningGrid,
    generate_simple_wall_layout,
    generate_wall_layout_with_openings,
)


def _covered_cells(layout):
    catalog = create_m0_brick_catalog()
    covered = set()
    for placement in layout.placements:
        brick = catalog.get(placement.brick_id)
        width, depth = brick.footprint(placement.rotation_quarter_turns)
        assert depth == 1
        course = placement.z_plates // 3
        for x in range(placement.x_studs, placement.x_studs + width):
            assert (x, course) not in covered
            covered.add((x, course))
    return covered


def _blocked_cells(openings):
    return {
        (x, z)
        for opening in openings
        for z in range(opening.z_bricks, opening.z_end)
        for x in range(opening.x_studs, opening.x_end)
    }


def _joint_positions(layout, course):
    catalog = create_m0_brick_catalog()
    placements = sorted(
        (p for p in layout.placements if p.z_plates == course * 3),
        key=lambda p: p.x_studs,
    )
    joints = set()
    for placement in placements:
        brick = catalog.get(placement.brick_id)
        width, _ = brick.footprint(placement.rotation_quarter_turns)
        joint = placement.x_studs + width
        if 0 < joint < layout.wall_width_studs:
            joints.add(joint)
    return joints


def test_door_opening_is_left_empty():
    opening = WallOpeningGrid(
        id="door",
        x_studs=6,
        z_bricks=0,
        width_studs=4,
        height_bricks=3,
    )
    layout = generate_wall_layout_with_openings(16, 6, [opening])
    expected = {(x, z) for z in range(6) for x in range(16)} - _blocked_cells([opening])
    assert _covered_cells(layout) == expected


def test_window_floats_above_lower_courses():
    opening = WallOpeningGrid(
        id="window",
        x_studs=5,
        z_bricks=2,
        width_studs=6,
        height_bricks=2,
    )
    layout = generate_wall_layout_with_openings(16, 6, [opening])
    covered = _covered_cells(layout)
    assert all((x, 0) in covered and (x, 1) in covered for x in range(16))
    assert all((x, 2) not in covered and (x, 3) not in covered for x in range(5, 11))
    assert all((x, 4) in covered for x in range(16))


def test_multiple_openings_have_exact_allowed_cell_coverage():
    openings = [
        WallOpeningGrid(id="door", x_studs=2, z_bricks=0, width_studs=3, height_bricks=3),
        WallOpeningGrid(id="window", x_studs=9, z_bricks=2, width_studs=4, height_bricks=2),
    ]
    layout = generate_wall_layout_with_openings(16, 6, openings)
    expected = {(x, z) for z in range(6) for x in range(16)} - _blocked_cells(openings)
    assert _covered_cells(layout) == expected


def test_no_brick_crosses_an_opening():
    opening = WallOpeningGrid(id="window", x_studs=7, z_bricks=1, width_studs=2, height_bricks=3)
    layout = generate_wall_layout_with_openings(16, 5, [opening])
    catalog = create_m0_brick_catalog()
    for placement in layout.placements:
        course = placement.z_plates // 3
        brick = catalog.get(placement.brick_id)
        width, _ = brick.footprint(placement.rotation_quarter_turns)
        if opening.z_bricks <= course < opening.z_end:
            assert placement.x_studs + width <= opening.x_studs or placement.x_studs >= opening.x_end


@pytest.mark.parametrize(
    "opening",
    [
        WallOpeningGrid(id="bad", x_studs=15, z_bricks=0, width_studs=2, height_bricks=1),
        WallOpeningGrid(id="bad", x_studs=0, z_bricks=5, width_studs=1, height_bricks=2),
    ],
)
def test_out_of_bounds_openings_are_rejected(opening):
    with pytest.raises(ValidationError):
        generate_wall_layout_with_openings(16, 6, [opening])


def test_overlapping_openings_are_rejected():
    openings = [
        WallOpeningGrid(id="a", x_studs=2, z_bricks=1, width_studs=5, height_bricks=3),
        WallOpeningGrid(id="b", x_studs=5, z_bricks=2, width_studs=4, height_bricks=2),
    ]
    with pytest.raises(ValidationError):
        generate_wall_layout_with_openings(16, 6, openings)


def test_touching_openings_are_allowed():
    openings = [
        WallOpeningGrid(id="a", x_studs=2, z_bricks=1, width_studs=3, height_bricks=2),
        WallOpeningGrid(id="b", x_studs=5, z_bricks=1, width_studs=3, height_bricks=2),
    ]
    layout = generate_wall_layout_with_openings(16, 5, openings)
    expected = {(x, z) for z in range(5) for x in range(16)} - _blocked_cells(openings)
    assert _covered_cells(layout) == expected


def test_duplicate_opening_ids_are_rejected():
    openings = [
        WallOpeningGrid(id="x", x_studs=1, z_bricks=0, width_studs=2, height_bricks=1),
        WallOpeningGrid(id="x", x_studs=5, z_bricks=0, width_studs=2, height_bricks=1),
    ]
    with pytest.raises(ValidationError):
        generate_wall_layout_with_openings(16, 4, openings)


def test_simple_wall_remains_backward_compatible():
    layout = generate_simple_wall_layout(16, 2)
    first_course = [p for p in layout.placements if p.z_plates == 0]
    assert [p.brick_id for p in first_course] == ["BRICK_1X8", "BRICK_1X8"]
    assert layout.openings == []


def test_joint_staggering_remains_without_openings():
    layout = generate_simple_wall_layout(16, 4)
    for course in range(1, 4):
        assert _joint_positions(layout, course - 1).isdisjoint(_joint_positions(layout, course))


def test_opening_layout_is_deterministic():
    openings = [
        WallOpeningGrid(id="window", x_studs=4, z_bricks=2, width_studs=5, height_bricks=2)
    ]
    first = generate_wall_layout_with_openings(17, 6, openings)
    second = generate_wall_layout_with_openings(17, 6, openings)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
