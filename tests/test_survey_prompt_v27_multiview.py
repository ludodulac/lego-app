from pathlib import Path


def test_v27_does_not_equate_more_views_with_certainty() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "La quantité de vues augmente les preuves, pas automatiquement la certitude" in source
    assert "Une hypothèse plausible ne doit ni disparaître ni devenir certaine" in source
