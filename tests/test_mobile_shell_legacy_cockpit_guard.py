from pathlib import Path


LOADER = Path("frontend/photo-shell-loader.js").read_text(encoding="utf-8")
PACKAGE = Path("frontend/brickhouse-survey-package.js").read_text(encoding="utf-8")


def test_legacy_cockpit_rewrite_is_not_loaded_over_single_screen_shell():
    assert "photo-shell.js" not in LOADER
    assert "photo-shell.css" not in LOADER
    assert "survey-import-feedback-guard.js" in LOADER


def test_shell_loader_cache_key_moves_forward_after_cockpit_removal():
    assert "photo-shell-loader.js?v=single-screen-0.9" in PACKAGE
