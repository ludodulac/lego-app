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


def test_validate_scene_reports_exact_missing_roof_pitch() -> None:
    response = client.post("/api/v1/validate-scene", json=_scene())
    assert response.status_code == 200
    payload = response.json()
    assert payload["projection"]["blocked"] is True
    assert payload["required_inputs"] == [{
        "object_id": "roof_main",
        "field": "pitch_degrees",
        "kind": "exact_metric",
        "reason": "shed_construction_requires_exact_pitch",
        "known_range_degrees": {"min": 10.0, "max": 35.0},
    }]


def test_validate_scene_against_survey_reports_same_missing_input() -> None:
    response = client.post(
        "/api/v1/validate-scene-against-survey",
        json={"survey": _survey(), "scene": _scene()},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid_for_projection"] is False
    assert payload["required_inputs"] == [{
        "object_id": "roof_main",
        "field": "pitch_degrees",
        "kind": "exact_metric",
        "reason": "shed_construction_requires_exact_pitch",
        "known_range_degrees": {"min": 10.0, "max": 35.0},
    }]
