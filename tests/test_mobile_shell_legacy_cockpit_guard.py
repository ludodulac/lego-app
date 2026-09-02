from pathlib import Path


LOADER = Path("frontend/photo-shell-loader.js").read_text(encoding="utf-8")
PACKAGE = Path("frontend/brickhouse-survey-package.js").read_text(encoding="utf-8")
STATE_JS = Path("frontend/mobile-shell-state.js").read_text(encoding="utf-8")


def test_restored_interface_keeps_cockpit_and_import_feedback_loaded():
    assert "photo-shell.js" in LOADER
    assert "photo-shell.css" in LOADER
    assert "survey-import-feedback-guard.js" in LOADER


def test_restored_shell_avoids_the_later_competing_focus_layer():
    assert "requestedView" not in STATE_JS
    assert "dataset.shellPanel" not in STATE_JS
    assert "photo-shell-loader.js?v=single-screen-1.0" in PACKAGE
