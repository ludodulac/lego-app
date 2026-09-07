from pathlib import Path


AUDIT = Path("frontend/scene-handoff-ownership-audit-v47.js")
ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_scene_handoff_ownership_audit_blocks_external_context_primitives():
    text = AUDIT.read_text(encoding="utf-8")

    assert 'subject_ownership="external_context"' in text
    assert "NEVER create a target Scene primitive" in text
    assert "volumes, roofs, chimneys, openings, equipment, stairs or platforms" in text


def test_scene_handoff_ownership_audit_blocks_uncertain_ownership_metrification():
    text = AUDIT.read_text(encoding="utf-8")

    assert 'subject_ownership="unresolved"' in text
    assert "plausible/unproven" in text
    assert "do not metrify it as target geometry" in text


def test_scene_handoff_ownership_audit_is_loaded_after_output_frame():
    text = ENTRY.read_text(encoding="utf-8")
    output_index = text.index("scene-handoff-output-frame-v46.js")
    ownership_index = text.index("scene-handoff-ownership-audit-v47.js")

    assert ownership_index > output_index
