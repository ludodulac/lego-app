from pathlib import Path


def test_v27_keeps_facade_is_gable_as_separate_hypothesis() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "`attributes.facade_is_gable:true`" in source
