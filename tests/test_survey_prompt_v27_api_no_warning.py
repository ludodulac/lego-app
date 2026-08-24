import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_fresh_external_roof_loss_is_not_warning_only() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    issues=TestClient(app).post("/api/v1/validate-survey",json=payload).json()["issues"]
    assert all(i["severity"]!="warning" for i in issues if i["code"]=="multiview_roof_missing_shape_hypothesis")
