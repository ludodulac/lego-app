from pathlib import Path


def test_v27_keeps_exterior_material_vocabulary() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for value in ("timber","concrete","masonry","stone","metal","composite","unknown"):
        assert value in source
