from pathlib import Path

PROMPT = Path(__file__).resolve().parents[1] / "frontend" / "brickhouse-survey-prompt.txt"


def test_survey_prompt_requires_multiview_roof_shape_preflight() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "RELEVÉ ARCHITECTURAL v2.7" in source
    assert "PRÉFLIGHT TOITURE MULTI-VUES" in source
    assert "multiview_roof_missing_shape_hypothesis" in source
    assert "roof_type" in source
    assert "facade_is_gable" in source
    assert "sans inventer pitch, hauteur ou axe métrique" in source
