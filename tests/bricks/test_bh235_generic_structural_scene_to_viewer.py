import json
from pathlib import Path

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "generic_scene_structural_capabilities.json"


def _placement_ids(parts):
    return [part["placement_id"] if isinstance(part, dict) else part.placement_id for part in parts]


def test_resolved_platform_support_railing_and_masonry_stair_survive_to_viewer_export() -> None:
    scene = ArchitecturalScene.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)
    brick_ids = _placement_ids(bundle.brick_model.parts)

    # Platform open railing: scene_architecture emits rail cells and
    # scene_railing_solutions compacts their top runs without erasing posts.
    assert any(value.startswith("scene-platform:deck:x_min:rail-top-solution:") for value in brick_ids)
    assert any(value.startswith("scene-platform:deck:x_min:rail-post:") for value in brick_ids)

    # Metric SupportPost: scene_architecture emits support cells and
    # scene_support_solutions exact-covers them with structural bricks.
    assert any(value.startswith("scene-platform:deck:support-solution:deck-post:") for value in brick_ids)

    # Masonry stair: scene_architecture emits the stepped body, treads and the
    # explicitly requested left parapet; existing solution passes may compact the
    # body/treads but must preserve their architectural provenance.
    assert any(value.startswith("scene-stair:deck-stair:body:solution:") for value in brick_ids)
    assert any(value.startswith("scene-stair:deck-stair:tread:solution:") for value in brick_ids)
    assert any(value.startswith("scene-stair:deck-stair:left-parapet:") for value in brick_ids)
    assert not any("scene-stair:deck-stair:right-parapet:" in value for value in brick_ids)

    # The viewer consumes this serialized BrickExportBundle. Prove the same
    # structural placements survive serialization instead of only existing in the
    # in-memory BrickModel.
    viewer_export = json.loads(json.dumps(bundle.model_dump(mode="json")))
    assert viewer_export["schema_version"] == "0.1"
    viewer_parts = viewer_export["brick_model"]["parts"]
    viewer_ids = _placement_ids(viewer_parts)
    assert viewer_export["bom"]["total_parts"] == len(viewer_parts)

    required_prefixes = (
        "scene-platform:deck:x_min:rail-top-solution:",
        "scene-platform:deck:x_min:rail-post:",
        "scene-platform:deck:support-solution:deck-post:",
        "scene-stair:deck-stair:body:solution:",
        "scene-stair:deck-stair:tread:solution:",
        "scene-stair:deck-stair:left-parapet:",
    )
    for prefix in required_prefixes:
        assert any(value.startswith(prefix) for value in viewer_ids), prefix
