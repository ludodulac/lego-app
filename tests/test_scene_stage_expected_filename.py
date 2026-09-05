from pathlib import Path


def test_scene_generator_keeps_scene_pdf_filename():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf" in text
