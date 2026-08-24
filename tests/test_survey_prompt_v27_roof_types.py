from pathlib import Path


def test_v27_lists_scene_supported_roof_categories() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for value in ("flat","gable","hip","shed","mansard","gambrel","butterfly","other"):
        assert value in source
