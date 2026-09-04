from pathlib import Path


def test_pipeline_wires_facade_rhythm_fidelity_after_window_anchor_application():
    text = Path("backend/brickhouse/pipeline.py").read_text(encoding="utf-8")
    assert "from brickhouse.bricks.facade_rhythm_export import facade_rhythm_fidelity_issues" in text
    assert "application = apply_architectural_window_anchors(building, shell)" in text
    assert "*facade_rhythm_fidelity_issues(application)" in text
