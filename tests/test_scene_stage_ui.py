from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scene_stage_ui_hides_survey_export_and_waits_for_scene_button():
    ui = (ROOT / "frontend/scene-stage-ui.js").read_text(encoding="utf-8")
    assert "download-ai-package" in ui
    assert "surveyButton.hidden = true" in ui
    assert "surveyButton.disabled = true" in ui
    assert "Créer le PDF unique Survey → Scene" in ui
    assert "download-scene-handoff" in ui


def test_scene_entry_injects_scene_only_ui():
    scene = (ROOT / "frontend/scene.html").read_text(encoding="utf-8")
    assert "scene-stage-ui.js" in scene
    assert "</body>" in scene
