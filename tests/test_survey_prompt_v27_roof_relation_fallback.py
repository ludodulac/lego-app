from pathlib import Path


def test_v27_allows_qualitative_roof_edge_relation_when_full_shape_unknown() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "facade_roof_relationship" in source
    assert "roof_edge_type" in source
