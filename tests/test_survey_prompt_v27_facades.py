from pathlib import Path


def test_v27_keeps_four_facade_vocabulary() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "front|rear|left|right" in source
