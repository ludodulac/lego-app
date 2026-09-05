from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'


def text(name):
    return (FRONTEND / name).read_text(encoding='utf-8')


def test_global_menu_lists_every_user_facing_page():
    nav = text('site-nav.js')
    for target in (
        './index.html',
        './photo.html',
        './scene.html?benchmark=real-house-5&stage=scene',
        './configurator.html',
        './viewer.html',
        './instructions.html',
        './scene-viewer.html',
        './brickhouse-first-bricks.html',
        './brickhouse-reference-preview.html',
        './brickhouse-rich-scene-preview.html',
    ):
        assert target in nav
    assert "aria-controls', 'site-menu-panel'" in nav
    assert "aria-label', 'Navigation principale'" in nav
    assert "event.key === 'Escape'" in nav


def test_closed_menu_cannot_block_underlying_page_controls():
    nav = text('site-nav.js')
    assert '.site-nav-root{position:fixed' in nav
    assert 'pointer-events:none' in nav
    assert '.site-nav-toggle{' in nav and 'pointer-events:auto' in nav
    assert '.site-nav-panel{' in nav and 'pointer-events:auto' in nav
    assert '.site-nav-panel[hidden]{display:none;pointer-events:none}' in nav
    assert 'z-index:2147483000' not in nav


def test_primary_handoff_actions_have_unambiguous_names():
    nav = text('site-nav.js')
    scene = text('scene.html')
    assert 'Créer le PDF Photos → Relevé' in nav
    assert 'Créer le PDF Relevé → Scene 3D' in nav
    assert 'Créer le PDF Relevé → Scene 3D' in scene
    assert 'Créer le PDF unique Survey → Scene' not in scene


def test_menu_is_loaded_by_all_user_facing_pages():
    assert "site-nav.js?v=bh147-global-nav-1" in text('app.js')
    assert "site-nav.js?v=bh147-global-nav-1" in text('brickhouse-survey-package.js')
    for page in (
        'scene.html',
        'configurator.html',
        'viewer.html',
        'instructions.html',
        'scene-viewer.html',
        'brickhouse-first-bricks.html',
        'brickhouse-reference-preview.html',
        'brickhouse-rich-scene-preview.html',
    ):
        assert "site-nav.js?v=bh147-global-nav-1" in text(page), page
