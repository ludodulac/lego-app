from pathlib import Path


def test_v27_keeps_landing_to_building_boundary_relation() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "palier→`building_boundary`" in source
