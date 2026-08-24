import json
from pathlib import Path


def test_fresh_external_fixture_uses_photo_evidence_objects() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    roof=payload["observations"][0]
    assert all(set(e)>={"photo_index","observation"} for e in roof["evidence"])
