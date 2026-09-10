from pathlib import Path


AUDIT = Path("frontend/scene-handoff-contract-audit-v44.js")


def test_scene_handoff_requires_backend_appearance_root_without_invention():
    text = AUDIT.read_text(encoding="utf-8")

    assert 'root MUST contain "appearance"' in text
    assert '"appearance": {}' in text
    assert "NEVER invent colors, materials or style" in text
    assert "absence of evidence must remain absence of a claim" in text


def test_scene_handoff_appearance_rule_is_generic():
    text = AUDIT.read_text(encoding="utf-8")

    assert "real-house-5" not in text
