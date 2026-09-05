from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_photo_page_loads_nav_through_package_without_fullscreen_nav_hitbox():
    package = (ROOT / 'frontend' / 'brickhouse-survey-package.js').read_text(encoding='utf-8')
    nav = (ROOT / 'frontend' / 'site-nav.js').read_text(encoding='utf-8')
    assert "import './site-nav.js" in package
    assert '.site-nav-root{position:fixed' in nav
    assert 'pointer-events:none' in nav
    assert 'z-index:2147483000' not in nav
