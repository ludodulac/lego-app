import json
from pathlib import Path


def test_fresh_external_fixture_roof_has_multiple_evidence_views_but_no_shape_attrs() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    roof=next(item for item in payload["observations"] if item["kind"]=="roof")
    assert len({e["photo_index"] for e in roof["evidence"]})>=2
    assert not roof.get("attributes")
