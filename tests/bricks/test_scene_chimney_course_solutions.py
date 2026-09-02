from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_chimney_course_solutions import compact_scene_chimney_courses
from brickhouse.bricks.scene_chimneys import augment_brick_model_with_scene_chimneys
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.9}


def _scene():
    prop = lambda value: {"value": value, "source": SOURCE, "evidence": []}
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-chimney-courses",
        "name": "Generic chimney courses",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "width": prop(8.0),
            "depth": prop(6.0),
            "height": prop(4.0),
            "floors": 1,
            "source": SOURCE,
        }],
        "chimneys": [{
            "id": "chimney-a",
            "position": {"x": 2.0, "y": 2.0, "z": 3.0},
            "width": 0.5,
            "depth": 1.0,
            "height": 1.0,
            "source": SOURCE,
        }],
        "appearance": {},
    })


def _chimney_cell(placement_id, x, y, z=12):
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X1",
        category="brick",
        component="facade_detail",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
    )


def _model(parts):
    return BrickModel(
        building_id="generic",
        volume_id="main",
        width_studs=32,
        depth_studs=24,
        height_plates=60,
        parts=parts,
    )


def _course(*, z=12, missing=None, index_start=1):
    missing = missing or set()
    parts = []
    index = index_start
    for dx in range(2):
        for dy in range(4):
            if (dx, dy) in missing:
                continue
            parts.append(
                _chimney_cell(
                    f"scene-chimney:chimney-a:{index:05d}",
                    8 + dx,
                    8 + dy,
                    z=z,
                )
            )
            index += 1
    return parts


def test_full_two_by_four_course_becomes_one_structural_brick():
    result = compact_scene_chimney_courses(_model(_course()), _scene())
    assert len(result.parts) == 1
    part = result.parts[0]
    assert part.part_id == "BRICK_2X4"
    assert part.rotation_quarter_turns == 0
    assert (part.x_studs, part.y_studs, part.z_plates) == (8, 8, 12)
    assert part.placement_id.startswith("scene-chimney:chimney-a:")


def test_separate_vertical_courses_never_merge():
    source = [
        *_course(z=12, index_start=1),
        *_course(z=15, index_start=20),
    ]
    result = compact_scene_chimney_courses(_model(source), _scene())
    assert len(result.parts) == 2
    assert {part.z_plates for part in result.parts} == {12, 15}
    assert {part.part_id for part in result.parts} == {"BRICK_2X4"}


def test_missing_generated_cell_remains_a_hard_hole():
    source = _course(missing={(0, 1)})
    result = compact_scene_chimney_courses(_model(source), _scene())

    covered = set()
    spans = {
        "BRICK_2X3": (2, 3),
        "BRICK_2X2": (2, 2),
        "BRICK_1X4": (1, 4),
        "BRICK_1X3": (1, 3),
        "BRICK_1X2": (1, 2),
        "BRICK_1X1": (1, 1),
    }
    for part in result.parts:
        width, depth = spans[part.part_id]
        if part.rotation_quarter_turns % 2:
            width, depth = depth, width
        covered.update(
            (part.x_studs + dx, part.y_studs + dy)
            for dx in range(width)
            for dy in range(depth)
        )

    expected = {(8 + dx, 8 + dy) for dx in range(2) for dy in range(4)} - {(8, 9)}
    assert covered == expected
    assert (8, 9) not in covered


def test_renderer_exact_covers_selected_two_by_four_footprint_per_course():
    base = _model([
        BrickModelPart(
            placement_id="base-wall-cell",
            part_id="BRICK_1X1",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade=Facade.FRONT,
        )
    ])
    scene = _scene()
    before = scene.model_dump(mode="json", by_alias=True)

    result = augment_brick_model_with_scene_chimneys(base, scene, front_width_studs=32)
    chimney_parts = [
        part for part in result.parts
        if part.placement_id.startswith("scene-chimney:chimney-a:")
    ]

    assert chimney_parts
    assert {part.part_id for part in chimney_parts} == {"BRICK_2X4"}
    assert len({part.z_plates for part in chimney_parts}) == len(chimney_parts)
    assert scene.model_dump(mode="json", by_alias=True) == before
