from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "verify-deployed-photo-checkpoint.yml"


def test_deployed_photo_checkpoint_proves_fresh_benchmark_pdf_path() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "fresh five-photo benchmark through PDF generation" in source
    assert "benchmark=real-house-5" in source
    assert "selected-photo-preview" in source
    assert "expect_download" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.10.pdf" in source
    assert "brickhouse-survey-result.json" in source
    assert "pendingArchitecturalSurvey" not in source
    assert "bh230-restored" not in source
