import json
from pathlib import Path


def test_fresh_external_fixture_keeps_user_front_width_anchor() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    m=payload["known_measurements"][0]
    assert (m["kind"],m["value"],m["units"])==("front_width",10,"m")
