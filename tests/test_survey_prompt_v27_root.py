from pathlib import Path


def test_v27_keeps_architectural_survey_root_fields() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for field in ("schema_version","id","name","canonical_frame","photos","known_measurements","observations","relations","representation_policy","notes"):
        assert field in source
