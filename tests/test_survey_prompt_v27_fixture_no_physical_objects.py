import json
from pathlib import Path


def test_fresh_external_fixture_has_no_legacy_physical_objects_root() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    assert "physical_objects" not in payload
