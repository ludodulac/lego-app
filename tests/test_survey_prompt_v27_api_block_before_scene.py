import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_fresh_external_roof_loss_stops_at_survey_gate_before_scene_fusion() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is False
