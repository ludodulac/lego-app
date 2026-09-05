from pathlib import Path


def test_scene_stage_does_not_offer_survey_pdf():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.10" not in text
    assert "download-ai-package" not in text
