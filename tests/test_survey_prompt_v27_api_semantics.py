import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_blocks_fresh_multiview_roof_information_loss() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    response=TestClient(app).post("/api/v1/validate-survey",json=payload)
    assert response.status_code==200
    body=response.json()
    assert body["valid_for_scene_fusion"] is False
    assert "multiview_roof_missing_shape_hypothesis" in {i["code"] for i in body["issues"]}
