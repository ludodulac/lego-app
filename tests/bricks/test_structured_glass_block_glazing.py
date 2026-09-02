import pytest

from brickhouse.bricks.scene_glazing import _is_glass_block, augment_brick_model_with_scene_glazing
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def _scene(*, glazing: str | None, evidence_text: str | None = None) -> ArchitecturalScene:
    source = {"kind": "observed", "confidence": 0.95}
    metric_source = {"kind": "inferred", "confidence": 0.9}
    prop = lambda value: {"value": value, "source": metric_source, "evidence": []}
    opening = {
        "id": "opening-a",
        "type": "window",
        "volume_id": "main",
        "facade": "front",
        "offset_horizontal": 1.25,
        "offset_vertical": 0.6,
        "width": 0.75,
        "height": 0.6,
        "source": source,
        "evidence": (
            [{"photo_index": 1, "observation": evidence_text}]
            if evidence_text is not None
            else []
        ),
    }
    if glazing is not None:
        opening["opening_visual"] = {"glazing": glazing}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "structured-glazing",
            "name": "Generic structured glazing fixture",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "width": prop(7.5),
                    "depth": prop(5.5),
                    "height": prop(4.5),
                    "floors": 1,
                    "source": metric_source,
                    "evidence": [],
                }
            ],
            "openings": [opening],
            "appearance": {},
        }
    )


@pytest.mark.parametrize(
    "glazing",
    ["glass block", "glass_blocks", "glass-block", "pavé de verre", "pavés_de_verre"],
)
def test_structured_glass_block_vocabulary_is_authoritative_positive(glazing: str) -> None:
    scene = _scene(glazing=glazing)

    assert _is_glass_block(scene.openings[0]) is True


def test_structured_non_block_glazing_suppresses_stale_glass_block_prose() -> None:
    scene = _scene(
        glazing="clear_glass",
        evidence_text="Earlier observation called this a glass block opening.",
    )

    assert _is_glass_block(scene.openings[0]) is False

    model = BrickModel(
        building_id="generic",
        volume_id="main",
        width_studs=30,
        depth_studs=22,
        height_plates=30,
        parts=[],
    )
    augmented = augment_brick_model_with_scene_glazing(model, scene, front_width_studs=30)
    assert not [
        part
        for part in augmented.parts
        if part.placement_id.startswith("scene-glazing:opening-a:")
    ]


def test_legacy_evidence_text_still_recognizes_glass_blocks_without_structured_field() -> None:
    scene = _scene(glazing=None, evidence_text="Small opening filled with glass blocks.")

    assert _is_glass_block(scene.openings[0]) is True


def test_structured_glass_block_augmentation_preserves_scene_and_uses_existing_pane_path() -> None:
    scene = _scene(glazing="glass_block")
    before = scene.model_dump(mode="json")
    model = BrickModel(
        building_id="generic",
        volume_id="main",
        width_studs=30,
        depth_studs=22,
        height_plates=30,
        parts=[],
    )

    augmented = augment_brick_model_with_scene_glazing(model, scene, front_width_studs=30)
    glazing_parts = [
        part
        for part in augmented.parts
        if part.placement_id.startswith("scene-glazing:opening-a:")
    ]

    assert glazing_parts
    assert {part.part_id for part in glazing_parts} == {"BRICK_1X1"}
    assert {part.category for part in glazing_parts} == {"window_pane"}
    assert scene.model_dump(mode="json") == before


def test_scene_pipeline_renders_structured_glass_block_without_matching_prose() -> None:
    scene = _scene(glazing="pavés de verre")
    before = scene.model_dump(mode="json")

    bundle = run_m0_pipeline_scene(scene, front_width_studs=30)
    glazing_parts = [
        part
        for part in bundle.brick_model.parts
        if part.placement_id.startswith("scene-glazing:opening-a:")
    ]

    assert glazing_parts
    assert {part.part_id for part in glazing_parts} == {"BRICK_1X1"}
    assert scene.model_dump(mode="json") == before
