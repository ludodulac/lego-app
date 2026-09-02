from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_materials import apply_scene_part_categories
from brickhouse.bricks.scene_stair_body_solutions import compact_scene_stair_bodies
from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.9}


def _scene():
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-stair-body-solutions",
        "name": "Generic stair body solutions",
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
        "stairs": [{
            "id": "stair-a",
            "start": {"x": 12, "y": 2, "z": 0},
            "end": {"x": 10, "y": 2, "z": 1},
            "width": 1.2,
            "material": "concrete",
            "source": SOURCE,
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def _body(placement_id, x, y, z=0, *, category="brick"):
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
        width_studs=48,
        depth_studs=40,
        height_plates=60,
        parts=parts,
    )


def _rectangle(*, x0=10, y0=5, width=2, depth=4, z=0, index_start=1):
    index = index_start
    parts = []
    for dx in range(width):
        for dy in range(depth):
            parts.append(_body(f"scene-stair:stair-a:body:{index:05d}", x0 + dx, y0 + dy, z))
            index += 1
    return parts


def test_two_by_four_body_course_becomes_one_structural_brick():
    result = compact_scene_stair_bodies(_model(_rectangle()), _scene())
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_2X4"
    assert part.rotation_quarter_turns == 0
    assert (part.x_studs, part.y_studs, part.z_plates) == (10, 5, 0)
    assert part.placement_id.startswith("scene-stair:stair-a:body:")


def test_long_x_body_course_preserves_orientation():
    result = compact_scene_stair_bodies(
        _model(_rectangle(width=4, depth=2)),
        _scene(),
    )
    assert len(result.parts) == 1
    assert result.parts[0].part_id == "BRICK_2X4"
    assert result.parts[0].rotation_quarter_turns == 1


def test_body_courses_at_different_heights_never_merge():
    parts = [
        *_rectangle(z=0, index_start=1),
        *_rectangle(z=3, index_start=20),
    ]
    result = compact_scene_stair_bodies(_model(parts), _scene())
    assert len(result.parts) == 2
    assert {part.z_plates for part in result.parts} == {0, 3}
    assert {part.part_id for part in result.parts} == {"BRICK_2X4"}


def test_irregular_body_never_bridges_a_missing_source_cell():
    parts = [
        _body("scene-stair:stair-a:body:00001", 10, 5),
        _body("scene-stair:stair-a:body:00002", 11, 5),
        _body("scene-stair:stair-a:body:00003", 13, 5),
        _body("scene-stair:stair-a:body:00004", 14, 5),
    ]
    result = compact_scene_stair_bodies(_model(parts), _scene())
    assert len(result.parts) == 2
    assert {part.part_id for part in result.parts} == {"BRICK_1X2"}
    assert {(part.x_studs, part.y_studs) for part in result.parts} == {(10, 5), (13, 5)}


def test_material_stage_compacts_body_and_preserves_concrete_semantics():
    source = _model(_rectangle())
    result = apply_scene_part_categories(source, _scene())
    assert len(result.parts) == 1
    assert result.parts[0].part_id == "BRICK_2X4"
    assert result.parts[0].category == "concrete"
    assert len(source.parts) == 8
    assert all(part.category == "brick" for part in source.parts)


def test_tread_and_edge_parts_are_left_for_their_own_solution_layers():
    tread = _body("scene-stair:stair-a:tread:00001", 10, 5)
    parapet = _body("scene-stair:stair-a:left-parapet:00002", 10, 5, z=6)
    model = _model([tread, parapet])
    result = compact_scene_stair_bodies(model, _scene())
    assert result is model
