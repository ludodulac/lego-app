from pathlib import Path


def test_v27_attribute_certainty_only_references_present_attributes() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "`attribute_certainty` ne référence que des clés présentes dans `attributes`" in source
