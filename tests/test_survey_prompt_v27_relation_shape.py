from pathlib import Path


def test_v27_keeps_relation_ids_and_distinct_endpoints() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for field in ("subject_id","object_id","certainty","statement","evidence"):
        assert field in source
    assert "observations distinctes" in source
