from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_materials import apply_scene_part_categories
from brickhouse.bricks.scene_support_solutions import compact_scene_platform_supports
from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.9}


def _scene(*, two_supports=False):
    supports = [{
        "id": "post-a",
        "position": {"x": 10.2, "y": 2.2, "z": 0.0},
        "width": 0.4,
        "depth": 0.8,
        "height": 1.0,
        "source": SOURCE,
    }]
    if two_supports:
        supports.append({
            "id": "post-b",
            "position": {"x": 10.8, "y": 2.2, "z": 0.0},
            "width": 0.4,
            "depth": 0.8,
            "height": 1.0,
            "source": SOURCE,
        })
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-support-solutions",
        "name": "Generic support solutions",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": [{
            "id": "deck",
            "position": {"x": 10, "y": 2, "z": 1},
            "width": 2,
            "depth": 4,
            "thickness": 0.2,
            "material": "timber",
            "supports": supports,
            "source": SOURCE,
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def _support_cell(placement_id, x, y, z=0, *, category="brick"):
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X1",
        category=category,
        component="facade_detail",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=0,
        facade=Facade.RIGHT,
    )


def _model(parts):
    return BrickModel(
        building_id="generic",
        volume_id="main",
        width_studs=40,
        depth_studs=32,
        height_plates=60,
        parts=parts,
    )


def _rect_support_cells(*, support=1, x0=10, y0=5, width=2, depth=4, z=0):
    return [
        _support_cell(
            f"scene-platform:deck:support{support}:{dx}:{dy}:{z:04d}",
            x0 + dx,
            y0 + dy,
            z,
        )
        for dx in range(width)
        for dy in range(depth)
    ]


def test_two_by_four_support_course_becomes_one_structural_brick():
    result = compact_scene_platform_supports(
        _model(_rect_support_cells()),
        _scene(),
    )
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_2X4"
    assert part.rotation_quarter_turns == 0
    assert (part.x_studs, part.y_studs, part.z_plates) == (10, 5, 0)
    assert ":support-solution:post-a:" in part.placement_id


def test_support_orientation_is_preserved_for_long_x_footprint():
    result = compact_scene_platform_supports(
        _model(_rect_support_cells(width=4, depth=2)),
        _scene(),
    )
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_2X4"
    assert part.rotation_quarter_turns == 1
    assert (part.x_studs, part.y_studs) == (10, 5)


def test_support_courses_at_different_heights_are_never_joined():
    parts = [
        *_rect_support_cells(z=0),
        *_rect_support_cells(z=3),
    ]
    result = compact_scene_platform_supports(_model(parts), _scene())
    assert len(result.parts) == 2
    assert {part.z_plates for part in result.parts} == {0, 3}
    assert {part.part_id for part in result.parts} == {"BRICK_2X4"}


def test_different_declared_supports_are_never_joined_even_when_adjacent():
    parts = [
        *_rect_support_cells(support=1, x0=10, y0=5, width=2, depth=2),
        *_rect_support_cells(support=2, x0=12, y0=5, width=2, depth=2),
    ]
    result = compact_scene_platform_supports(_model(parts), _scene(two_supports=True))
    assert len(result.parts) == 2
    assert {part.part_id for part in result.parts} == {"BRICK_2X2"}
    assert any(":post-a:" in part.placement_id for part in result.parts)
    assert any(":post-b:" in part.placement_id for part in result.parts)


def test_compactor_never_bridges_missing_source_cells():
    parts = [
        _support_cell("scene-platform:deck:support1:0:0:0000", 10, 5),
        _support_cell("scene-platform:deck:support1:1:0:0000", 11, 5),
        _support_cell("scene-platform:deck:support1:3:0:0000", 13, 5),
        _support_cell("scene-platform:deck:support1:4:0:0000", 14, 5),
    ]
    result = compact_scene_platform_supports(_model(parts), _scene())
    assert len(result.parts) == 2
    assert {part.part_id for part in result.parts} == {"BRICK_1X2"}
    assert {(part.x_studs, part.y_studs) for part in result.parts} == {(10, 5), (13, 5)}


def test_scene_material_stage_applies_support_solution_and_preserves_material_semantics():
    source_model = _model(_rect_support_cells())
    result = apply_scene_part_categories(source_model, _scene())
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_2X4"
    assert part.category == "timber"
    assert source_model.parts[0].category == "brick"
    assert len(source_model.parts) == 8


def test_non_support_parts_are_left_untouched():
    ordinary = _support_cell("scene-platform:deck:deck:00001", 10, 5)
    model = _model([ordinary])
    result = compact_scene_platform_supports(model, _scene())
    assert result is model
