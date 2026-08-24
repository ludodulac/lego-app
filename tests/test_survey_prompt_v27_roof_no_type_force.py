from pathlib import Path


def test_v27_requires_supported_hypothesis_not_forced_roof_type() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "si ces indices soutiennent une catégorie de forme" in source
    assert "relation de rive est lisible" in source
