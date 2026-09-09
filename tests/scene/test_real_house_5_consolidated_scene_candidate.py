import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene import ArchitecturalScene, analyze_multi_run_stair_geometry
from brickhouse.survey import ArchitecturalSurvey

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SCENE_FIXTURE = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
CLIENT = TestClient(app)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_recipe() -> ArchitecturalScene:
    recipe = _load(BENCHMARK / "scene-candidate-v0.2.json")
    payload = _load(SCENE_FIXTURE)

    for overlay_name in recipe["apply_overlays_in_order"]:
        overlay = _load(BENCHMARK / overlay_name)
        if overlay["operation"] == "replace_stair_system_geometry":
            replaced = set(overlay["replaces_scene_stair_ids"])
            payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
            payload["stairs"].extend(deepcopy(overlay["stairs"]))
            payload["stair_system_links"] = deepcopy(overlay["stair_system_links"])
            updates = {item["relation_id"]: item for item in overlay["relation_updates"]}
            for relation in payload.get("relations", []):
                if relation["id"] in updates:
                    update = updates[relation["id"]]
                    relation.update({key: update[key] for key in ("subject_id", "object_id", "geometry_status", "statement")})
        elif overlay["operation"] == "update_platform_geometry":
            updates = {item["platform_id"]: item for item in overlay["platform_updates"]}
            for platform in payload.get("platforms", []):
                update = updates.get(platform["id"])
                if update:
                    platform["position"]["z"] = update["position_z"]
                    platform["source"] = deepcopy(update["source"])
                    platform["evidence"] = deepcopy(update["evidence"])
                    for support in platform.get("supports", []):
                        support["height"] = update["support_height"]
                        support["source"] = deepcopy(update["source"])
        else:
            raise AssertionError(f"unsupported benchmark overlay operation: {overlay['operation']}")

    payload["id"] = recipe["scene_id"]
    payload["name"] = "BrickHouse real-house-5 consolidated Scene candidate v0.2"
    return ArchitecturalScene.model_validate(payload)


def test_consolidated_recipe_materializes_current_benchmark_geometry() -> None:
    scene = _materialize_recipe()
    recipe = _load(BENCHMARK / "scene-candidate-v0.2.json")
    scale = _load(BENCHMARK / "front-width-scale-estimate.json")
    provenance = _load(BENCHMARK / "scene-candidate-v0.2-provenance.json")

    main = next(item for item in scene.volumes if item.id == "volume_main")
    timber = next(item for item in scene.platforms if item.id == "platform-timber-1")
    landing = next(item for item in scene.platforms if item.id == "platform-massive-1")

    assert scale["min_m"] <= main.width.value <= scale["max_m"]
    assert main.width.value == recipe["retained_metric_values"]["volume_main.width_m"]
    assert recipe["metric_status"]["volume_main.depth_m"].startswith("provisional")
    assert recipe["metric_status"]["volume_main.height_m"].startswith("provisional")
    assert provenance["known_measurements_required"] is False
    assert timber.position.z < landing.position.z
    assert len(scene.stairs) >= 2
    assert len(scene.stair_system_links) == 2


def test_consolidated_recipe_builds_lego_without_new_measurements() -> None:
    survey = ArchitecturalSurvey.model_validate(_load(BENCHMARK / "accepted-survey-v0.1.json"))
    scene = _materialize_recipe()
    report = analyze_multi_run_stair_geometry(survey, scene)
    stair = next(item for item in report.facts if item.observation_id == "stair-exterior-1")

    assert survey.known_measurements == []
    assert stair.connected is True
    assert stair.spanning_path_exists is True
    assert stair.direction_change_realized is True

    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": scene.model_dump(mode="json"), "front_width_studs": 48, "allow_partial": True},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["brick_model"]["parts"]
    assert result["bom"]["total_parts"] == len(result["brick_model"]["parts"])
    assert result["assembly_plan"]["steps"]
