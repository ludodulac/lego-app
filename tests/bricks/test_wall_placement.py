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


def _course_spans(layout, course):
    catalog = create_m0_brick_catalog()
    placements = [p for p in layout.placements if p.z_plates == course * 3]
    placements.sort(key=lambda p: p.x_studs)
    return [catalog.get(p.brick_id).footprint(p.rotation_quarter_turns)[0] for p in placements]


def _course_joints(layout, course):
    spans = _course_spans(layout, course)
    joints = set()
    x = 0
    for span in spans[:-1]:
        x += span
        joints.add(x)
    return joints


def test_16_by_6_wall_staggers_adjacent_courses():
    layout = generate_simple_wall_layout(16, 6)
    assert _course_spans(layout, 0) == [8, 8]
    assert _course_spans(layout, 1) == [6, 8, 2]
    for course in range(1, 6):
        assert _course_joints(layout, course - 1).isdisjoint(_course_joints(layout, course))


def test_17_wide_first_course_falls_back_to_1x1():
    layout = generate_simple_wall_layout(17, 1)
    assert [p.brick_id for p in layout.placements] == [
        "BRICK_1X8",
        "BRICK_1X8",
        "BRICK_1X1",
    ]
    assert [p.x_studs for p in layout.placements] == [0, 8, 16]


def test_10_wide_first_course_uses_8_plus_2():
    layout = generate_simple_wall_layout(10, 1)
    assert [p.brick_id for p in layout.placements] == ["BRICK_1X8", "BRICK_1X2"]


@pytest.mark.parametrize("width,height", [(13, 4), (16, 6), (17, 5)])
def test_wall_has_exact_coverage_without_overlap(width, height):
    layout = generate_simple_wall_layout(width, height)
    cells = _covered_cells(layout)
    assert len(cells) == width * height
    assert len(set(cells)) == width * height
    assert set(cells) == {(x, z) for z in range(height) for x in range(width)}


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
