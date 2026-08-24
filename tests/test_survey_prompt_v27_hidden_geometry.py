from pathlib import Path


def test_v27_forbids_hidden_completion() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "aucune zone cachée complétée" in source
    assert "complétion cachée" in source
