from pathlib import Path


PHOTO_HTML = Path("frontend/photo.html").read_text(encoding="utf-8")
SCENE_BUILD_JS = Path("frontend/scene-build.js").read_text(encoding="utf-8")
INDEX_HTML = Path("frontend/index.html").read_text(encoding="utf-8")


def test_photo_page_has_no_competing_mobile_shell_layer():
    assert "mobile-shell.css" not in PHOTO_HTML
    assert "shell-progress" not in PHOTO_HTML
    assert "mobile-shell-nav" not in PHOTO_HTML
    assert 'data-boldungo-shell="single-screen"' not in PHOTO_HTML


def test_scene_build_does_not_load_mobile_shell_state():
    assert "mobile-shell-state.js" not in SCENE_BUILD_JS
    assert "scene-required-inputs.js" in SCENE_BUILD_JS
    assert "partial-scene-build.js" in SCENE_BUILD_JS


def test_original_photo_workflow_entry_copy_is_restored():
    assert "Décrire ma maison" in INDEX_HTML
    assert "Analyser des photos" in INDEX_HTML
    assert "Prototype prêt" in INDEX_HTML
