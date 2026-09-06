from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "capture-deployed-viewer-screenshots.yml"


def test_screenshot_workflow_runs_only_after_successful_main_pages() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'workflows: ["Deploy viewer to GitHub Pages"]' in source
    assert "types: [completed]" in source
    assert "workflow_run.conclusion == 'success'" in source
    assert "workflow_run.head_branch == 'main'" in source
    assert "workflow_run.head_sha" in source


def test_screenshot_workflow_exercises_public_scene_to_viewer_path() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "scene.html?benchmark=real-house-5&stage=scene" in source
    assert "#scene-import-result" in source
    assert "#scene-build-bricks" in source
    assert "wait_for_url('**/viewer.html*'" in source
    assert "brickhouse.currentExport" in source
    assert "/api/v1/" not in source


def test_screenshot_workflow_captures_canonical_views_and_artifact() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    for filename in ("perspective.png", "front.png", "rear.png", "left.png", "right.png"):
        assert filename.split(".")[0] in source
    for selector in ("#reset-view", "#view-front", "#view-rear", "#view-left", "#view-right"):
        assert selector in source
    assert "actions/upload-artifact@v4" in source
    assert "real-house-5-viewer-${{ github.event.workflow_run.head_sha }}" in source
    assert "viewer-screenshots/" in source
