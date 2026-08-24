import json
from pathlib import Path


def test_fresh_external_fixture_has_no_fabricated_roof_metrics() -> None:
    path=Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json"
    payload=json.loads(path.read_text(encoding="utf-8"))
    roof=next(item for item in payload["observations"] if item["kind"]=="roof")
    attrs=roof.get("attributes",{})
    assert "pitch_degrees" not in attrs
    assert "height" not in attrs
