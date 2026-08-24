from pathlib import Path


def test_v27_keeps_observe_before_measure_rule() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Observe avant de mesurer" in source
