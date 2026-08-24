from pathlib import Path

PROMPT = Path(__file__).resolve().parents[1] / "frontend" / "brickhouse-survey-prompt.txt"


def test_survey_v27_requires_nonmetric_multiview_roof_preflight() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "RELEVÉ ARCHITECTURAL v2.7" in source
    assert "PRÉFLIGHT TOITURE MULTI-VUES — OBLIGATOIRE" in source
    assert "roof_type:\"other\"" in source
    assert "n’autorise aucune métrique" in source
    assert "toute toiture recoupée dans au moins deux photos" in source
