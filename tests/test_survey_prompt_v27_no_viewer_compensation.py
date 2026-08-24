from pathlib import Path


def test_v27_forbids_viewer_orientation_compensation() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Aucune compensation viewer" in source
