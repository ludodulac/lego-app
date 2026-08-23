from pathlib import Path

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


FIXTURE = Path("docs/examples/architectural-scene-rich-exterior.json")


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


def test_generic_rich_scene_fixture_builds_without_losing_exterior_primitives():
    bundle = run_m0_pipeline_scene(_scene(), front_width_studs=48)
    ids = {part.placement_id for part in bundle.brick_model.parts}

    assert any(value.startswith("scene-platform:deck:") for value in ids)
    assert any(value.startswith("scene-stair:deck_stair:") for value in ids)
    assert any(value.startswith("scene-terrain:right:") for value in ids)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)


def test_generic_rich_scene_fixture_preserves_architectural_opening_metadata():
    scene = _scene()
    opening = scene.openings[0]

    assert opening.id == "front_window"
    assert opening.facade.value == "front"
    assert opening.width == 1.2
    assert opening.height == 1.5
    assert opening.has_sill is True
    assert opening.has_decorative_surround is True


def test_generic_rich_scene_fixture_has_distinct_material_and_terrain_semantics():
    scene = _scene()

    assert scene.platforms[0].material.value == "timber"
    assert scene.stairs[0].material.value == "concrete"
    assert scene.terrain is not None
    assert scene.terrain.profiles[0].outward_extent == 1.5
