import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
RECIPE = BENCHMARK / "scene-candidate-v0.2.json"
CLIENT = TestClient(app)


def test_materializer_resolves_real_house_recipe_without_hidden_geometry() -> None:
    scene = materialize_scene_recipe(RECIPE)

    timber = next(item for item in scene.platforms if item.id == "platform-timber-1")
    landing = next(item for item in scene.platforms if item.id == "platform-massive-1")
    stair_ids = {item.id for item in scene.stairs}
    glazed_door = next(item for item in scene.openings if item.id == "front-opening-6")

    assert scene.id == "brickhouse-scene-real-house-5-candidate-v0.2"
    assert timber.position.z < landing.position.z
    assert {"stair-exterior-1-run-lower-v1", "stair-exterior-1-run-upper-v1"} <= stair_ids
    assert len(scene.stair_system_links) == 2
    assert glazed_door.type.value == "door"
    assert glazed_door.opening_visual is not None
    assert glazed_door.opening_visual.glazing == "glazed"
    # User confirmation changes semantics only; metric geometry stays photo-derived.
    assert glazed_door.source.kind.value == "inferred"
    assert glazed_door.width == 1.65
    assert glazed_door.height == 2.25


def test_materialized_scene_emits_viewer_compatible_partial_export_bundle(tmp_path: Path) -> None:
    scene = materialize_scene_recipe(RECIPE)
    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": scene.model_dump(mode="json"), "front_width_studs": 48, "allow_partial": True},
    )
    assert response.status_code == 200, response.text
    bundle = response.json()
    parts = bundle["brick_model"]["parts"]
    placement_ids = [part["placement_id"] for part in parts]
    fidelity = {(issue["code"], issue.get("object_id")) for issue in bundle["fidelity_issues"]}
    glazed_door_parts = [part for part in parts if part.get("opening_id") == "front-opening-6"]

    assert parts
    assert bundle["bom"]["total_parts"] == len(parts)
    assert bundle["assembly_plan"]["steps"]
    assert any(value.startswith("volume-exterior-1:") for value in placement_ids)
    assert any(value.startswith("scene-platform:platform-timber-1:") for value in placement_ids)
    assert any("stair-exterior-1-run-lower-v1" in value for value in placement_ids)
    assert any("stair-exterior-1-run-upper-v1" in value for value in placement_ids)
    assert any(value.startswith("scene-chimney:chimney-1:") for value in placement_ids)
    assert glazed_door_parts
    assert all(part["category"] == "window_pane" for part in glazed_door_parts)
    assert ("lego_architectural_opening_unrepresented", "front-opening-6") not in fidelity
    assert any(part["category"] == "roof_tile" for part in parts)
    assert any(
        part["placement_id"].startswith("scene-platform:platform-timber-1:")
        and part["category"] == "timber"
        for part in parts
    )
    assert any(
        "stair-exterior-1-run-lower-v1" in part["placement_id"]
        and part["category"] == "masonry"
        for part in parts
    )
    assert ("partial_preview_secondary_volume_omitted", "volume-exterior-1") not in fidelity
    assert ("partial_preview_roof_omitted", "roof-1") not in fidelity
    assert ("partial_preview_exterior_object_omitted", "chimney-1") not in fidelity

    output = tmp_path / "real-house-5-viewer-export.json"
    output.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    assert output.stat().st_size > 0
