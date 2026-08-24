from pathlib import Path


def test_v27_reaudits_roof_before_emitting_invalid_output() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "ré-audite les preuves avant sortie" in source
