import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_reports_roof_loss_as_error() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    issue=next(i for i in body["issues"] if i["code"]=="multiview_roof_missing_shape_hypothesis")
    assert issue["severity"]=="error"
    assert issue["observation_id"]=="roof_main_01"
