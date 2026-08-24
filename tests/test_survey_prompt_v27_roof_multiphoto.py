from pathlib import Path


def test_v27_defines_multiview_roof_using_distinct_photo_evidence() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "`evidence` cite au moins deux photos différentes" in source
