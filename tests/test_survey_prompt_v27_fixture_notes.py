import json
from pathlib import Path


def test_fresh_external_fixture_documents_exact_regression() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    assert "roof existence survived" in payload["notes"]
    assert "shape hypotheses were discarded" in payload["notes"]
