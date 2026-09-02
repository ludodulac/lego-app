from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_materials import apply_scene_part_categories
from brickhouse.bricks.scene_stair_solutions import compact_scene_stair_treads
from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.9}


def _scene(*, y_axis=False):
    start = {"x": 12, "y": 2, "z": 0} if not y_axis else {"x": 10, "y": 4, "z": 0}
    end = {"x": 10, "y": 2, "z": 1}
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-stair-solutions",
        "name": "Generic stair solutions",
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
            "start": start,
            "end": end,
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


def _tread(placement_id, x, y, z=6, *, category="brick"):
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


def test_x_axis_stair_width_becomes_one_y_oriented_tread_brick():
    parts = [
        _tread(f"scene-stair:stair-a:tread:{i:05d}", 20, 7 + i)
        for i in range(4)
    ]
    result = compact_scene_stair_treads(_model(parts), _scene())
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_1X4"
    assert part.rotation_quarter_turns == 0
    assert (part.x_studs, part.y_studs, part.z_plates) == (20, 7, 6)


def test_y_axis_stair_width_becomes_one_x_oriented_tread_brick():
    parts = [
        _tread(f"scene-stair:stair-a:tread:{i:05d}", 7 + i, 20)
        for i in range(4)
    ]
    result = compact_scene_stair_treads(_model(parts), _scene(y_axis=True))
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_1X4"
    assert part.rotation_quarter_turns == 1
    assert (part.x_studs, part.y_studs) == (7, 20)


def test_different_steps_never_merge_when_they_share_a_quantized_height():
    parts = [
        *[
            _tread(f"scene-stair:stair-a:tread:{i:05d}", 20, 7 + i, z=6)
            for i in range(3)
        ],
        *[
            _tread(f"scene-stair:stair-a:tread:{10 + i:05d}", 21, 7 + i, z=6)
            for i in range(3)
        ],
    ]
    result = compact_scene_stair_treads(_model(parts), _scene())
    assert len(result.parts) == 2
    assert {part.part_id for part in result.parts} == {"BRICK_1X3"}
    assert {part.x_studs for part in result.parts} == {20, 21}


def test_missing_tread_cell_remains_a_hard_gap():
    parts = [
        _tread("scene-stair:stair-a:tread:00001", 20, 7),
        _tread("scene-stair:stair-a:tread:00002", 20, 8),
        _tread("scene-stair:stair-a:tread:00003", 20, 10),
        _tread("scene-stair:stair-a:tread:00004", 20, 11),
    ]
    result = compact_scene_stair_treads(_model(parts), _scene())
    assert len(result.parts) == 2
    assert {part.part_id for part in result.parts} == {"BRICK_1X2"}
    assert {part.y_studs for part in result.parts} == {7, 10}


def test_material_stage_compacts_tread_and_preserves_stair_material():
    source = _model([
        _tread(f"scene-stair:stair-a:tread:{i:05d}", 20, 7 + i)
        for i in range(4)
    ])
    result = apply_scene_part_categories(source, _scene())
    assert len(result.parts) == 1
    assert result.parts[0].part_id == "BRICK_1X4"
    assert result.parts[0].category == "concrete"
    assert len(source.parts) == 4
    assert all(part.category == "brick" for part in source.parts)


def test_masonry_body_and_edge_parts_are_not_reinterpreted_as_treads():
    body = _tread("scene-stair:stair-a:body:00001", 20, 7)
    rail = _tread("scene-stair:stair-a:left-rail:00002", 20, 7, z=12)
    model = _model([body, rail])
    result = compact_scene_stair_treads(model, _scene())
    assert result is model
