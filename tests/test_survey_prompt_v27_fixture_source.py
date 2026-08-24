import json
from pathlib import Path


def test_fresh_external_fixture_uses_sourceinfo_objects() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    assert all(isinstance(p["source"],dict) for p in payload["photos"])
    assert isinstance(payload["known_measurements"][0]["source"],dict)
