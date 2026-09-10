from pathlib import Path


AUDIT = Path("frontend/scene-handoff-ownership-audit-v47.js")
ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_scene_handoff_ownership_audit_blocks_external_context_primitives():
    text = AUDIT.read_text(encoding="utf-8")

    assert 'subject_ownership="external_context"' in text
    assert "NEVER create a target Scene primitive" in text
    assert "volumes, roofs, chimneys, openings, equipment, stairs or platforms" in text


def test_scene_handoff_ownership_audit_preserves_uncertainty_without_erasing_certain_target_linked_objects():
    text = AUDIT.read_text(encoding="utf-8")

    assert "plausible/unproven" in text
    assert "NEVER promote it to target_building" in text
    assert "do not let that uncertain attribute erase an observation whose object existence is certain" in text
    assert "certain relation chain anchored to the target building" in text
    assert "keep the ownership uncertainty explicit" in text
    assert "Never use this rule for an observation whose ownership is certainly external_context" in text


def test_scene_handoff_ownership_audit_is_loaded_after_output_frame():
    text = ENTRY.read_text(encoding="utf-8")
    output_index = text.index("scene-handoff-output-frame-v46.js")
    ownership_index = text.index("scene-handoff-ownership-audit-v47.js")

    assert ownership_index > output_index
