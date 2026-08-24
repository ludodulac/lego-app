from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.scene import ArchitecturalScene


def test_glazed_door_adds_panes_without_inventing_perimeter_frame() -> None:
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "glazed_door_scene",
        "name": "Glazed door scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": 0.7}},
            "height": {"value": 5, "source": {"kind": "inferred", "confidence": 0.7}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": 0.7},
        }],
        "openings": [{
            "id": "front_glazed_door",
            "type": "door",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 4,
            "offset_vertical": 0,
            "width": 1.5,
            "height": 2.2,
            "source": {"kind": "inferred", "confidence": 0.7},
            "evidence": [{"photo_index": 1, "observation": "Large glazed door visible"}],
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })
    model = BrickModel(
        building_id="glazed_door_scene",
        volume_id="main",
        width_studs=48,
        depth_studs=38,
        height_plates=60,
        parts=[],
    )

    enriched = augment_brick_model_with_scene_glazing(model, scene, front_width_studs=48)
    generated = [part for part in enriched.parts if part.placement_id.startswith("scene-glazing:front_glazed_door:")]

    assert generated
    assert {part.category for part in generated} == {"window_pane"}
