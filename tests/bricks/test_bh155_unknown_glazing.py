from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.6}


def _scene(*, glazing: str | None, evidence: str = "Large low opening visible.") -> ArchitecturalScene:
    opening = {
        "id": "glazed_unknown_opening",
        "type": "unknown",
        "volume_id": "main",
        "facade": "front",
        "offset_horizontal": 4.0,
        "offset_vertical": 0.0,
        "width": 1.8,
        "height": 2.3,
        "source": SOURCE,
        "evidence": [{"photo_index": 1, "observation": evidence}],
    }
    if glazing is not None:
        opening["opening_visual"] = {
            "glazing": glazing,
            "joinery_confidence": "unknown",
        }
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "bh155-unknown-glazing",
            "name": "Unknown glazed opening",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 7.2, "source": SOURCE},
                    "depth": {"value": 9.0, "source": SOURCE},
                    "height": {"value": 8.0, "source": SOURCE},
                    "floors": 3,
                    "source": SOURCE,
                }
            ],
            "openings": [opening],
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "dark_brown"},
            },
        }
    )


def _model() -> BrickModel:
    return BrickModel(
        building_id="bh155-unknown-glazing",
        volume_id="main",
        width_studs=48,
        depth_studs=60,
        height_plates=160,
        parts=[
            BrickModelPart(
                placement_id="seed",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade="front",
            )
        ],
    )


def _generated(scene: ArchitecturalScene):
    enriched = augment_brick_model_with_scene_glazing(_model(), scene, front_width_studs=48)
    return [part for part in enriched.parts if part.placement_id.startswith("scene-glazing:glazed_unknown_opening:")]


def test_unknown_opening_with_structured_glazing_is_visually_represented_without_type_promotion():
    scene = _scene(glazing="clear glazed composition")

    generated = _generated(scene)

    assert scene.openings[0].type.value == "unknown"
    assert generated
    assert {part.category for part in generated} == {"window_pane"}
    assert {part.opening_id for part in generated} == {"glazed_unknown_opening"}


def test_unknown_opening_does_not_use_legacy_glazing_text_heuristic():
    scene = _scene(glazing=None, evidence="Large glazed door visible in legacy prose.")

    assert scene.openings[0].type.value == "unknown"
    assert not _generated(scene)


def test_unknown_opening_with_structured_negative_glazing_stays_unrepresented():
    scene = _scene(glazing="unknown", evidence="Large glazed door visible in legacy prose.")

    assert not _generated(scene)
