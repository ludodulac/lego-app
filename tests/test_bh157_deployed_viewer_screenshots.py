from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "verify-deployed-scene-api-e2e.yml"
DUPLICATE_WORKFLOW = ROOT / ".github" / "workflows" / "capture-deployed-viewer-screenshots.yml"


def test_screenshots_share_the_single_scene_api_e2e_build() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'workflows: ["Deploy viewer to GitHub Pages"]' in source
    assert "workflow_run.conclusion == 'success'" in source
    assert "workflow_run.head_branch == 'main'" in source
    assert "scene.html?benchmark=real-house-5&stage=scene" in source
    assert "#scene-import-result" in source
    assert "#scene-build-bricks" in source
    assert "wait_for_url('**/viewer.html*'" in source
    assert "brickhouse.currentExport" in source
    assert "/api/v1/" not in source
    assert not DUPLICATE_WORKFLOW.exists()


def test_scene_api_e2e_captures_canonical_views_and_artifact() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    for name in ("perspective", "front", "rear", "left", "right"):
        assert f"('{name}'," in source
    for selector in ("#reset-view", "#view-front", "#view-rear", "#view-left", "#view-right"):
        assert selector in source
    assert "canvas.screenshot" in source
    assert "actions/upload-artifact@v4" in source
    assert "real-house-5-viewer-${{ github.event.workflow_run.head_sha }}" in source
    assert "viewer-screenshots/" in source
