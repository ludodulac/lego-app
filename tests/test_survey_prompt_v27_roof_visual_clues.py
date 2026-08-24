from pathlib import Path


def test_v27_roof_preflight_cross_checks_visual_clues() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "silhouette, rives, pignons/égouts visibles" in source
    assert "continuité entre vues" in source
