from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.scene import ArchitecturalScene


def _scene(*, evidence: str, glazing=None) -> ArchitecturalScene:
    opening = {
        "id": "service_door",
        "type": "door",
        "volume_id": "main",
        "facade": "left",
        "offset_horizontal": 2,
        "offset_vertical": 0,
        "width": 1.2,
        "height": 2,
        "source": {"kind": "inferred", "confidence": .7},
        "evidence": [{"photo_index": 1, "observation": evidence}],
    }
    if glazing is not None:
        opening["opening_visual"] = {"glazing": glazing}
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "door-scene",
        "name": "Door scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": .7}},
            "height": {"value": 5, "source": {"kind": "inferred", "confidence": .7}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .7},
        }],
        "openings": [opening],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def _model() -> BrickModel:
    return BrickModel(
        building_id="door-scene",
        volume_id="main",
        width_studs=48,
        depth_studs=38,
        height_plates=60,
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


def _generated(scene: ArchitecturalScene):
    enriched = augment_brick_model_with_scene_glazing(_model(), scene, front_width_studs=48)
    return [
        part
        for part in enriched.parts
        if part.placement_id.startswith("scene-glazing:service_door:")
    ]


def test_explicit_non_glazed_door_is_not_filled_with_scene_glazing():
    assert not _generated(_scene(evidence="Grande ouverture non vitrée d’accès."))


def test_structured_glazing_generates_door_panes_without_text_keyword():
    generated = _generated(_scene(evidence="Porte d’accès principale.", glazing="clear"))
    assert generated
    assert {part.category for part in generated} == {"window_pane"}
    assert {part.opening_id for part in generated} == {"service_door"}


def test_structured_negative_glazing_overrides_misleading_legacy_text():
    assert not _generated(_scene(evidence="Ancienne note: glazed door.", glazing="unglazed"))


def test_structured_unknown_glazing_does_not_invent_geometry_from_legacy_text():
    assert not _generated(_scene(evidence="Possibly glazed door.", glazing="unknown"))


def test_absent_structured_glazing_preserves_legacy_text_fallback():
    generated = _generated(_scene(evidence="Large glazed door visible."))
    assert generated
    assert {part.opening_id for part in generated} == {"service_door"}
