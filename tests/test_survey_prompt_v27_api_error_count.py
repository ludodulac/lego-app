import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_fresh_external_roof_loss_has_one_blocking_error() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    issues=TestClient(app).post("/api/v1/validate-survey",json=payload).json()["issues"]
    assert sum(i["severity"]=="error" for i in issues)==1
