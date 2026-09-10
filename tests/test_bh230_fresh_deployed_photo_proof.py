from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "verify-deployed-photo-checkpoint.yml"


def test_deployed_photo_checkpoint_proves_returning_browser_resets_to_fresh_benchmark() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "returning browser resets to fresh five-photo benchmark and stays responsive" in source
    assert "benchmark=real-house-5" in source
    assert "accepted-survey-v0.1.json" in source
    assert "brickhouse.pendingArchitecturalSurvey" in source
    assert "localStorage.getItem('brickhouse.pendingArchitecturalSurvey')" in source
    assert "get_attribute('data-shell-state') == 'photos'" in source
    assert "selected-photo-preview" in source
    assert "page.evaluate('1 + 1') == 2" in source
    assert "expect_download" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.10.pdf" in source
    assert "brickhouse-survey-result.json" in source
