from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / ".github" / "workflows" / "pages.yml"


def test_pages_redeploys_when_postdeploy_scene_workflows_change() -> None:
    source = PAGES.read_text(encoding="utf-8")
    expected = {
        ".github/workflows/verify-deployed-scene.yml",
        ".github/workflows/verify-deployed-scene-api-e2e.yml",
    }
    for path in expected:
        assert f"- '{path}'" in source
    assert "capture-deployed-viewer-screenshots.yml" not in source


def test_pages_trigger_remains_scoped_not_repository_wide() -> None:
    source = PAGES.read_text(encoding="utf-8")
    assert "paths:" in source
    assert "- '**'" not in source
    assert "- '.github/workflows/**'" not in source
