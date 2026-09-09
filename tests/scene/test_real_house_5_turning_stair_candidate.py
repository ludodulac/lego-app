import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene import ArchitecturalScene, analyze_multi_run_stair_geometry, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SURVEY_PATH = BENCHMARK / "accepted-survey-v0.1.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
OVERLAY_PATH = BENCHMARK / "turning-stair-scene-overlay-v0.1.json"
CLIENT = TestClient(app)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _survey_with_user_turn() -> tuple[ArchitecturalSurvey, ArchitecturalSurvey]:
    source = ArchitecturalSurvey.model_validate(_load(SURVEY_PATH))
    fact = HumanAttributeFact.model_validate(
        {
            "observation_id": "stair-exterior-1",
            "attribute_name": "stair_topology",
            "value": {
                "minimum_run_count": 2,
                "direction_change": True,
                "turning_node_kind": "turn_or_landing",
            },
            "certainty": "certain",
            "source": {"kind": "user_provided", "confidence": 1.0},
            "statement": "User confirms that the exterior stair changes direction.",
        }
    )
    candidate = apply_human_attribute_facts(source, [fact]).candidate
    return source, candidate


def _turning_scene() -> ArchitecturalScene:
    payload = _load(SCENE_PATH)
    overlay = _load(OVERLAY_PATH)
    replaced = set(overlay["replaces_scene_stair_ids"])
    payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
    payload["stairs"].extend(deepcopy(overlay["stairs"]))
    payload["stair_system_links"] = deepcopy(overlay["stair_system_links"])

    updates = {item["relation_id"]: item for item in overlay["relation_updates"]}
    for relation in payload.get("relations", []):
        update = updates.get(relation["id"])
        if update is None:
            continue
        relation["subject_id"] = update["subject_id"]
        relation["object_id"] = update["object_id"]
        relation["geometry_status"] = update["geometry_status"]
        relation["statement"] = update["statement"]

    return ArchitecturalScene.model_validate(payload)


def test_turning_overlay_realizes_user_confirmed_topology_without_mutating_survey() -> None:
    source, survey = _survey_with_user_turn()
    source_before = deepcopy(source.model_dump())
    scene = _turning_scene()

    report = analyze_multi_run_stair_geometry(survey, scene)
    fact = next(item for item in report.facts if item.observation_id == "stair-exterior-1")
    error_codes = {
        issue.code
        for issue in validate_scene_against_survey(survey, scene)
        if issue.severity.value == "error"
    }

    assert source.model_dump() == source_before
    assert source.known_measurements == []
    assert survey.known_measurements == []
    assert fact.component_run_ids == [
        "stair-exterior-1-run-lower-v1",
        "stair-exterior-1-run-upper-v1",
    ]
    assert fact.all_components_present is True
    assert fact.connected is True
    assert fact.spanning_path_exists is True
    assert fact.direction_change_realized is True
    assert "multi_run_stair_topology_unresolved" not in error_codes
    assert "multi_run_stair_direction_change_not_realized" not in error_codes
    assert "multi_run_stair_components_disconnected" not in error_codes


def test_turning_overlay_keeps_geometry_explicitly_low_confidence_and_revisable() -> None:
    overlay = _load(OVERLAY_PATH)

    assert len(overlay["stairs"]) == 2
    assert all(item["source"]["kind"] == "inferred" for item in overlay["stairs"])
    assert all(item["source"]["confidence"] < 0.25 for item in overlay["stairs"])
    assert "exact" not in overlay["inference_notes"][1].lower()
    assert any("not an exact" in note.lower() or "no exact" in note.lower() for note in overlay["inference_notes"])


def test_turning_scene_still_builds_a_conservative_partial_lego_preview() -> None:
    scene = _turning_scene()
    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": scene.model_dump(mode="json"), "front_width_studs": 48, "allow_partial": True},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["brick_model"]["parts"]
    assert payload["assembly_plan"]["steps"]
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
