from pathlib import Path


HTML = Path("frontend/scene-viewer.html")
JS = Path("frontend/scene-partial-build.js")


def test_scene_viewer_offers_first_trustworthy_lego_build() -> None:
    html = HTML.read_text(encoding="utf-8")
    script = JS.read_text(encoding="utf-8")

    assert 'id="build-partial-lego"' in html
    assert './scene-partial-build.js' in html
    assert '/api/v1/build-scene' in script
    assert 'allow_partial: true' in script
    assert "brickhouse.pendingExport" in script
    assert "./viewer.html" in script


def test_partial_build_reuses_same_scene_sources_as_architectural_preview() -> None:
    script = JS.read_text(encoding="utf-8")

    assert "brickhouse.previewArchitecturalScene" in script
    assert "brickhouse.pendingSceneValidation" in script
    assert "brickhouse.lastSceneSurveyValidation" in script
