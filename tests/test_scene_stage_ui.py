from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_scene_stage_ui_still_guards_survey_export_if_loaded():
    ui = (ROOT / "frontend/scene-stage-ui.js").read_text(encoding="utf-8")
    assert "download-ai-package" in ui
    assert "surveyButton.hidden = true" in ui
    assert "surveyButton.disabled = true" in ui
    assert "download-scene-handoff" in ui
    assert "ensureSceneButton" in ui


def test_legacy_scene_stage_ui_can_seed_accepted_checkpoint_without_api_round_trip():
    ui = (ROOT / "frontend/scene-stage-ui.js").read_text(encoding="utf-8")
    assert "real-house-5" in ui
    assert "accepted-survey-v0.1.json" in ui
    assert "accepted_repo_checkpoint" in ui
    assert "valid_for_scene_fusion: true" in ui
    assert "fetch(ACCEPTED_SURVEY_URL, { cache: 'no-store' })" in ui


def test_scene_entry_uses_dedicated_runtime_not_legacy_scene_ui():
    scene = (ROOT / "frontend/scene.html").read_text(encoding="utf-8")
    assert "scene-benchmark-runtime.js?v=bh147-scene-runtime-1" in scene
    assert "scene-stage-ui.js" not in scene
    assert "brickhouse-survey-package.js" not in scene
    assert "document.write" not in scene
    assert 'id="download-scene-handoff"' in scene
