import json
from pathlib import Path


def test_fresh_external_fixture_roof_is_seen_in_front_and_right_views() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    assert {e["photo_index"] for e in payload["observations"][0]["evidence"]}=={1,2}
