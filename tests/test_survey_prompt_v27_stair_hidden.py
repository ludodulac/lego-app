from pathlib import Path


def test_v27_does_not_complete_hidden_stair_flights() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Ne complète jamais une volée cachée" in source
