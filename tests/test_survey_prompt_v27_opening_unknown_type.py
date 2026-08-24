from pathlib import Path


def test_v27_keeps_certain_opening_when_type_is_only_plausible() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Si le type est seulement plausible, garde l'ouverture certaine" in source
