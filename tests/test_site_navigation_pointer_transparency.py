from pathlib import Path

NAV = (Path(__file__).resolve().parents[1] / 'frontend' / 'site-nav.js').read_text(encoding='utf-8')


def test_nav_container_is_pointer_transparent_but_controls_are_interactive():
    assert '.site-nav-root{position:fixed' in NAV
    assert 'font-family:system-ui,sans-serif;pointer-events:none}' in NAV
    assert '.site-nav-toggle{' in NAV
    assert 'font-size:0;pointer-events:auto}' in NAV
    assert '.site-nav-panel{' in NAV
    assert 'padding:12px;pointer-events:auto}' in NAV
    assert '.site-nav-panel[hidden]{display:none;pointer-events:none}' in NAV
