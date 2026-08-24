from pathlib import Path


def test_v27_roof_preflight_remains_non_metric() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "sans inventer pitch, hauteur ou axe métrique" in source
    assert "pixels→mètres" in source
    assert "Scene, BuildingModel, LEGO" in source
