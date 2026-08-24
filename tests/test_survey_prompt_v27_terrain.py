from pathlib import Path


def test_v27_keeps_terrain_slope_non_metric() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "slope_direction" in source
    assert "magnitude inconnue" in source
    assert "Aucun mètre inventé" in source
