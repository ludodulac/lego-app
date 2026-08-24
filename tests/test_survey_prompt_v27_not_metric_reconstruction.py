from pathlib import Path


def test_v27_remains_observation_before_reconstruction() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "sans reconstruction métrique et sans LEGO" in source
    assert "Observe avant de mesurer" in source
