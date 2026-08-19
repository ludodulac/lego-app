import pytest
from pydantic import ValidationError

from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.placement import generate_simple_wall_layout


def _covered_cells(layout):
    catalog = create_m0_brick_catalog()
    cells = []
    for placement in layout.placements:
        brick = catalog.get(placement.brick_id)
        width, depth = brick.footprint(placement.rotation_quarter_turns)
        assert depth == 1
        course = placement.z_plates // 3
        for x in range(placement.x_studs, placement.x_studs + width):
            cells.append((x, course))
    return cells


def test_16_by_6_wall_uses_two_1x8_bricks_per_course():
    layout = generate_simple_wall_layout(16, 6)
    assert len(layout.placements) == 12
    assert all(p.brick_id == "BRICK_1X8" for p in layout.placements)


def test_17_wide_wall_falls_back_to_1x1():
    layout = generate_simple_wall_layout(17, 1)
    assert [p.brick_id for p in layout.placements] == [
        "BRICK_1X8",
        "BRICK_1X8",
        "BRICK_1X1",
    ]
    assert [p.x_studs for p in layout.placements] == [0, 8, 16]


def test_10_wide_wall_uses_8_plus_2():
    layout = generate_simple_wall_layout(10, 1)
    assert [p.brick_id for p in layout.placements] == ["BRICK_1X8", "BRICK_1X2"]


def test_wall_has_exact_coverage_without_overlap():
    layout = generate_simple_wall_layout(13, 4)
    cells = _covered_cells(layout)
    assert len(cells) == 13 * 4
    assert len(set(cells)) == 13 * 4
    assert set(cells) == {(x, z) for z in range(4) for x in range(13)}


def test_each_course_starts_at_zero_and_uses_plate_height_grid():
    layout = generate_simple_wall_layout(9, 3)
    starts = {(p.z_plates, p.x_studs) for p in layout.placements if p.x_studs == 0}
    assert starts == {(0, 0), (3, 0), (6, 0)}
    assert all(p.z_plates % 3 == 0 for p in layout.placements)


def test_spanning_bricks_are_rotated_to_wall_axis():
    layout = generate_simple_wall_layout(8, 1)
    placement = layout.placements[0]
    assert placement.brick_id == "BRICK_1X8"
    assert placement.rotation_quarter_turns == 1


def test_single_stud_uses_unrotated_1x1():
    layout = generate_simple_wall_layout(1, 1)
    placement = layout.placements[0]
    assert placement.brick_id == "BRICK_1X1"
    assert placement.rotation_quarter_turns == 0


@pytest.mark.parametrize("width,height", [(0, 1), (-1, 1), (1, 0), (1, -1)])
def test_invalid_wall_dimensions_are_rejected(width, height):
    with pytest.raises(ValidationError):
        generate_simple_wall_layout(width, height)


def test_generation_is_deterministic():
    first = generate_simple_wall_layout(23, 5)
    second = generate_simple_wall_layout(23, 5)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
