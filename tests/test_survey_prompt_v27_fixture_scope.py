import json
from pathlib import Path


def test_fresh_external_fixture_is_minimal_reproduction_of_roof_loss() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    assert [o["kind"] for o in payload["observations"]]==["roof"]
    assert payload["known_measurements"][0]["value"]==10
