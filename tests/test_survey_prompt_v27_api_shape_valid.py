import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_fresh_external_v26_benchmark_reaches_semantic_validation_not_422() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    response=TestClient(app).post("/api/v1/validate-survey",json=payload)
    assert response.status_code==200
    assert response.json()["survey"]["canonical_frame"]["x_direction"]=="front_view_left_to_right"
