from pathlib import Path


def test_v27_preserves_plausible_roof_hypothesis_without_promoting_it() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Une hypothèse plausible ne doit ni disparaître ni devenir certaine" in source
