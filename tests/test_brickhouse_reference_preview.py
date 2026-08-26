from pathlib import Path


def test_pages_publishes_current_brickhouse_scene_fixture() -> None:
    workflow = Path('.github/workflows/pages.yml').read_text(encoding='utf-8')
    assert 'tests/fixtures/brickhouse_scene_current.json' in workflow
    assert 'frontend/brickhouse-scene-current.json' in workflow
    assert 'cp tests/fixtures/brickhouse_scene_current.json frontend/brickhouse-scene-current.json' in workflow


def test_reference_preview_loads_published_scene_without_mutating_it() -> None:
    loader = Path('frontend/brickhouse-reference-preview.js').read_text(encoding='utf-8')
    viewer = Path('frontend/scene-viewer.html').read_text(encoding='utf-8')
    assert "fetch('./brickhouse-scene-current.json'" in loader
    assert "localStorage.setItem('brickhouse.previewArchitecturalScene', JSON.stringify(scene))" in loader
    assert "window.location.replace('./scene-viewer.html')" in loader
    assert 'Charger la référence BrickHouse' in viewer
