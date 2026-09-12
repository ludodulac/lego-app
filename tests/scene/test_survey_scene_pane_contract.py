import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "generic_opening_pane_count_fidelity.json"
OUTPUT_FRAME = ROOT / "frontend" / "scene-handoff-output-frame-v46.js"


def _scene_payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["scene"]


def _serialized_opening(scene: ArchitecturalScene, opening_id: str):
    payload = scene.model_dump(mode="json")
    return next(item for item in payload["openings"] if item["id"] == opening_id)


def test_effective_scene_producer_contract_preserves_observed_pane_count_without_semantic_strengthening() -> None:
    contract = OUTPUT_FRAME.read_text(encoding="utf-8")

    assert "SceneOpening contract below also permits the field \"opening_visual\"" in contract
    assert "MUST preserve that exact observed integer" in contract
    assert "NEVER derive or strengthen leaf_count, pane_layout, window_style, or architectural PAIRED from pane_count" in contract
    assert "when the Survey has no observed opening topology, do not invent one" in contract


def test_scene_validation_and_serialization_keep_two_observed_panes_without_leaf_or_style_invention() -> None:
    scene = ArchitecturalScene.model_validate(_scene_payload())
    opening = _serialized_opening(scene, "window_two_visible_panes")

    assert opening["opening_visual"]["pane_count"] == 2
    assert opening["opening_visual"].get("leaf_count") is None
    assert opening.get("window_style") is None


def test_scene_validation_and_serialization_do_not_invent_unknown_topology() -> None:
    scene = ArchitecturalScene.model_validate(_scene_payload())
    opening = _serialized_opening(scene, "window_unknown_topology")

    opening_visual = opening.get("opening_visual")
    assert opening_visual is None or opening_visual.get("pane_count") is None
    if opening_visual is not None:
        assert opening_visual.get("leaf_count") is None
        assert opening_visual.get("pane_layout") is None
    assert opening.get("window_style") is None
