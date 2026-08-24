import json
from pathlib import Path
from fastapi.testclient import TestClient
from brickhouse.api import app


def test_roof_semantic_validation_does_not_mutate_missing_shape_into_guess() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    roof=next(o for o in body["survey"]["observations"] if o["id"]=="roof_main_01")
    assert roof["attributes"]=={}
    assert roof["attribute_certainty"]=={}
