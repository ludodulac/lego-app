from pathlib import Path


def test_scene_preview_keeps_bounded_roof_uncertain() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "pitch_range_degrees" in source
    assert "range.min_degrees" in source
    assert "range.max_degrees" in source
    assert "Les deux plans transparents montrent les limites, pas un angle choisi." in source
    assert "(range.min_degrees + range.max_degrees) / 2" not in source


def test_blocked_scene_links_to_architectural_preview() -> None:
    source = Path("frontend/scene-required-inputs.js").read_text(encoding="utf-8")
    assert "brickhouse.previewArchitecturalScene" in source
    assert "./scene-viewer.html" in source
    assert "Voir la reconstruction 3D actuelle" in source


def test_scene_preview_page_loads_dedicated_renderer() -> None:
    html = Path("frontend/scene-viewer.html").read_text(encoding="utf-8")
    assert "scene-viewer.js" in html
    assert "Aperçu architectural, pas encore une maquette LEGO" in html


def test_scene_preview_renders_known_exterior_elements() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "function renderPlatforms()" in source
    assert "function renderStairs()" in source
    assert "currentScene.platforms" in source
    assert "currentScene.stairs" in source
    assert "does not guess which sides receive posts or rails" in source
    assert "inventing individual steps" in source
    assert "Les détails non mesurés ne sont pas inventés." in source
