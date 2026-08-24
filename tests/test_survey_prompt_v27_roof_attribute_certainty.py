from pathlib import Path


def test_v27_requires_certainty_for_roof_hypotheses() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "`attribute_certainty.roof_type`" in source
    assert "`attribute_certainty.facade_is_gable`" in source
