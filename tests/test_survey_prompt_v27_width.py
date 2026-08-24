from pathlib import Path


def test_v27_keeps_front_width_as_only_known_measurement() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "uniquement `{ \"kind\":\"front_width\"" in source
