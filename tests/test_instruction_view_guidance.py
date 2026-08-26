from pathlib import Path


def test_notice_guidance_uses_backend_step_view_hint() -> None:
    script = Path("frontend/instruction-guidance.js").read_text(encoding="utf-8")
    styles = Path("frontend/instruction-guidance.css").read_text(encoding="utf-8")

    assert "step.view" in script
    assert "recommended-view-cue" in script
    assert "Orientation recommandée" in script
    assert "recommended-view-cue" in styles
