from pathlib import Path


def test_v27_keeps_roof_edge_fallback_cautious() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "avec sa prudence" in source
