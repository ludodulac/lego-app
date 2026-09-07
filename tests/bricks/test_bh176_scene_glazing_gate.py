from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_glazing_plan_safe import augment_brick_model_with_planned_scene_glazing
from brickhouse.scene import ArchitecturalScene


def _model() -> BrickModel:
    return BrickModel(
        building_id="bh176-gate",
        volume_id="main",
        width_studs=24,
        depth_studs=18,
        height_plates=45,
        parts=[BrickModelPart(
            placement_id="seed",
            part_id="BRICK_1X1",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade="front",
        )],
    )


def _scene(glazing: str) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh176-gate",
        "name": "Scene glazing gate",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "observed", "confidence": 0.9}},
            "depth": {"value": 7, "source": {"kind": "observed", "confidence": 0.9}},
            "height": {"value": 6, "source": {"kind": "observed", "confidence": 0.9}},
            "floors": 2,
            "source": {"kind": "observed", "confidence": 0.9},
        }],
        "openings": [{
            "id": "target",
            "type": "unknown",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2.0,
            "offset_vertical": 0.0,
            "width": 1.6,
            "height": 1.5,
            "source": {"kind": "observed", "confidence": 0.9},
            "opening_visual": {"glazing": glazing},
        }],
        "appearance": {},
    })


def test_clear_unknown_glazing_cannot_create_legacy_brick_cells_after_planning_boundary():
    model = augment_brick_model_with_planned_scene_glazing(
        _model(),
        _scene("clear"),
        front_width_studs=24,
    )

    assert not [part for part in model.parts if part.placement_id.startswith("scene-glazing:")]


def test_glass_block_glazing_keeps_its_dedicated_legacy_material_path_for_now():
    model = augment_brick_model_with_planned_scene_glazing(
        _model(),
        _scene("glass blocks"),
        front_width_studs=24,
    )

    generated = [part for part in model.parts if part.placement_id.startswith("scene-glazing:target:")]
    assert generated
    assert {part.part_id for part in generated} == {"BRICK_1X1"}
