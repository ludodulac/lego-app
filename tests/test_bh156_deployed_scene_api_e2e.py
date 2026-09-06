from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "verify-deployed-scene-api-e2e.yml"
PRELOAD = ROOT / "frontend" / "scene-benchmark-candidate-preload.js"


def test_scene_api_e2e_runs_only_after_successful_main_pages() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'workflows: ["Deploy viewer to GitHub Pages"]' in source
    assert "types: [completed]" in source
    assert "workflow_run.conclusion == 'success'" in source
    assert "workflow_run.head_branch == 'main'" in source
    assert "workflow_run.head_sha" in source


def test_scene_api_e2e_uses_public_ui_and_production_validation_flow() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "scene.html?benchmark=real-house-5&stage=scene" in source
    assert "#scene-import-result" in source
    assert "#scene-build-bricks" in source
    assert "wait_for_url('**/viewer.html*'" in source
    assert "brickhouse.pendingExport" in source
    assert "bom" in source
    assert "assembly_plan" in source
    assert "pageerror" in source
    assert "/api/v1/" not in source  # The browser must exercise the deployed UI, not bypass it.


def test_scene_preload_exposes_e2e_revision_marker() -> None:
    source = PRELOAD.read_text(encoding="utf-8")
    assert "jsonInput.dataset.sceneApiE2e = 'bh156'" in source
    assert "brickhouse-scene-real-house-5-candidate" in source
