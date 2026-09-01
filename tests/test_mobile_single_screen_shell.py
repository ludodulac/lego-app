from pathlib import Path


PHOTO_HTML = Path("frontend/photo.html").read_text(encoding="utf-8")
MOBILE_SHELL_CSS = Path("frontend/mobile-shell.css").read_text(encoding="utf-8")


def test_photo_workflow_exposes_single_screen_shell_without_replacing_existing_hooks():
    assert 'data-boldungo-shell="single-screen"' in PHOTO_HTML
    assert 'class="shell-progress"' in PHOTO_HTML
    assert 'class="mobile-shell-nav"' in PHOTO_HTML

    for anchor in (
        '#capture-card',
        '#measure-card',
        '#survey-handoff-card',
        '#analysis-panel',
        '#build-actions',
    ):
        assert anchor in PHOTO_HTML

    for existing_hook in (
        'id="guided-photo-grid"',
        'id="known-width"',
        'id="download-ai-package"',
        'id="external-analysis-file"',
        'id="import-analysis"',
        'id="scene-handoff-home"',
        'id="build-bricks"',
        'id="result"',
    ):
        assert existing_hook in PHOTO_HTML


def test_mobile_shell_is_additive_and_mobile_first():
    assert '<link rel="stylesheet" href="./photo.css" />' in PHOTO_HTML
    assert '<link rel="stylesheet" href="./mobile-shell.css" />' in PHOTO_HTML
    assert '@media(max-width:620px)' in MOBILE_SHELL_CSS
    assert 'position:fixed' in MOBILE_SHELL_CSS

    for existing_module in (
        './brickhouse-survey-package.js?v=pdf-handoff-0.8-scene-source-lock',
        './photo-simple.js?v=structured-capture-0.7',
        './external-bundle-import.js',
        './survey-import.js',
        './scene-handoff-photo-evidence.js?v=scene-handoff-0.2',
        './scene-chimney-compat.js?v=scene-chimney-compat-0.1',
        './photo.js',
        './scene-build.js',
    ):
        assert existing_module in PHOTO_HTML
