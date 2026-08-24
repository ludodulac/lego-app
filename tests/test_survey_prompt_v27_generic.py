from pathlib import Path


def test_v27_remains_generic_for_any_building() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Ce prompt doit fonctionner pour n’importe quel bâtiment" in source
