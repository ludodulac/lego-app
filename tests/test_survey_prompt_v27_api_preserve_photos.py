import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_blocked_roof_validation_preserves_photo_views() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["survey"]["photos"]==payload["photos"]
