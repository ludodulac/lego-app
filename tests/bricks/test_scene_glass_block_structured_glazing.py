import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.scene import ArchitecturalScene


ABSENT = object()


def _scene(*, glazing=ABSENT, evidence: str = "Opening observed.") -> ArchitecturalScene:
    opening = {
        "id": "glass_block_opening",
        "type": "window",
        "volume_id": "main",
        "facade": "front",
        "offset_horizontal": 2,
        "offset_vertical": 1,
        "width": 1.25,
        "height": 1.5,
        "source": {"kind": "inferred", "confidence": .8},
        "evidence": [{"photo_index": 1, "observation": evidence}],
    }
    if glazing is not ABSENT:
        opening["opening_visual"] = {"glazing": glazing}

    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "glass-block-scene",
        "name": "Glass block scene",
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
        building_id="glass-block-scene",
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
        part for part in enriched.parts
        if part.placement_id.startswith("scene-glazing:glass_block_opening:")
    ]


@pytest.mark.parametrize("glazing", [
    "glass block",
    "glass_blocks",
    "pavé-de-verre",
    "pavés de verre",
])
def test_structured_glass_block_vocabulary_renders_without_prose_keyword(glazing):
    scene = _scene(glazing=glazing, evidence="Translucent opening beside the entrance.")

    generated = _generated(scene)

    assert generated
    assert {part.part_id for part in generated} == {"BRICK_1X1"}
    assert {part.category for part in generated} == {"window_pane"}
    assert {part.opening_id for part in generated} == {"glass_block_opening"}


def test_structured_other_glazing_suppresses_stale_glass_block_prose():
    scene = _scene(glazing="clear", evidence="Legacy note: glass blocks at this opening.")

    assert not _generated(scene)


def test_structured_glass_block_vocabulary_is_exact_after_normalization():
    scene = _scene(glazing="glass blocks translucent", evidence="Legacy note: glass blocks.")

    assert not _generated(scene)


def test_missing_structured_glazing_keeps_legacy_glass_block_fallback():
    scene = _scene(evidence="Façade opening filled with pavés-de-verre.")

    assert _generated(scene)


def test_glass_block_rendering_does_not_mutate_scene():
    scene = _scene(glazing="glass_block", evidence="Structured observation only.")
    before = scene.model_dump(mode="json")

    assert _generated(scene)
    assert scene.model_dump(mode="json") == before
