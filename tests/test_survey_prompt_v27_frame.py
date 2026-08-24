from pathlib import Path


def test_v27_keeps_canonical_handedness() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "x=gauche→droite vu de face" in source
    assert "y=avant→arrière" in source
    assert "z=bas→haut" in source
