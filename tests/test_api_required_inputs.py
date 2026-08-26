import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)
FIXTURES = Path("tests/fixtures")


def _scene() -> dict:
    return json.loads((FIXTURES / "brickhouse_scene_current.json").read_text(encoding="utf-8"))


def _survey() -> dict:
    return json.loads((FIXTURES / "brickhouse_survey_current.json").read_text(encoding="utf-8"))


def expected_missing_roof_geometry() -> list[dict]:
    return [
        {"object_id": "roof_main", "field": "down_slope_direction", "kind": "categorical_geometry", "reason": "shed_construction_requires_fall_direction"},
        {"object_id": "roof_main", "field": "pitch_degrees", "kind": "exact_metric", "reason": "shed_construction_requires_exact_pitch"},
    ]


def test_validate_scene_reports_missing_roof_geometry_without_invented_range() -> None:
    response = client.post("/api/v1/validate-scene", json=_scene())
    assert response.status_code == 200
    payload = response.json()
    blockers = [issue for issue in payload["projection"]["issues"] if issue["severity"] == "blocker"]
    codes = [issue["code"] for issue in blockers]
    assert codes.count("shed_geometry_incomplete") == 1
    assert codes.count("topological_relation_geometry_unresolved") == 2
    assert payload["required_inputs"] == expected_missing_roof_geometry()


def test_validate_scene_against_survey_reports_same_missing_inputs() -> None:
    response = client.post(
        "/api/v1/validate-scene-against-survey",
        json={"survey": _survey(), "scene": _scene()},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid_for_projection"] is False
    assert payload["required_inputs"] == expected_missing_roof_geometry()
