from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "verify-deployed-scene.yml"
SCENE_HTML = ROOT / "frontend" / "scene.html"


def test_scene_runtime_workflow_runs_after_successful_pages_deploy() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'workflows: ["Deploy viewer to GitHub Pages"]' in source
    assert "types: [completed]" in source
    assert "workflow_run.conclusion == 'success'" in source
    assert "workflow_run.head_branch == 'main'" in source
    assert "workflow_run.head_sha" in source


def test_scene_runtime_workflow_checks_real_house_candidate_without_building_it() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "scene.html?benchmark=real-house-5&stage=scene" in source
    assert "brickhouse-scene-real-house-5-candidate" in source
    assert "data-preloaded-candidate-sha" in source
    assert "Candidat Scene BH-151 préchargé" in source
    assert "#scene-result-file" in source
    assert "#scene-import-result" in source
    assert "#scene-build-bricks" in source
    assert "is_disabled()" in source
    assert "pageerror" in source


def test_scene_page_exposes_runtime_marker_for_exact_deployment_check() -> None:
    html = SCENE_HTML.read_text(encoding="utf-8")
    assert '<meta name="brickhouse-scene-runtime-check" content="bh155" />' in html
