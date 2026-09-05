from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'


def test_every_page_exposed_by_menu_exists():
    nav = (FRONTEND / 'site-nav.js').read_text(encoding='utf-8')
    for page in (
        'index.html',
        'photo.html',
        'scene.html',
        'configurator.html',
        'viewer.html',
        'instructions.html',
        'scene-viewer.html',
        'brickhouse-first-bricks.html',
        'brickhouse-reference-preview.html',
        'brickhouse-rich-scene-preview.html',
    ):
        assert (FRONTEND / page).is_file()
        assert page in nav
