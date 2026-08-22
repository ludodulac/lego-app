from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"


def test_validate_survey_accepts_real_house_two_photo_fixture():
    client = TestClient(app)
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response = client.post("/api/v1/validate-survey", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["valid_for_scene_fusion"] is True
    assert body["issues"] == []
    survey = body["survey"]
    assert survey["schema_version"] == "0.1"
    assert survey["canonical_frame"]["x_direction"] == "front_view_left_to_right"
    assert survey["representation_policy"]["reproduce_weathering"] is False
    observation_ids = {item["id"] for item in survey["observations"]}
    assert "right_rising_road" in observation_ids
    assert "right_building_limit" in observation_ids


def test_validate_survey_rejects_missing_front_reference():
    client = TestClient(app)
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["photos"][0]["facade"] = "left"
    response = client.post("/api/v1/validate-survey", json=payload)
    assert response.status_code == 422
