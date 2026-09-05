from pathlib import Path


def test_scene_stage_explains_accepted_survey_is_frozen():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert "Le relevé validé est déjà figé" in text
