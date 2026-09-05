from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_active_package_wires_scene_stage_lock_after_v44_audit():
    package = (ROOT / "frontend/brickhouse-survey-package.js").read_text(encoding="utf-8")
    audit = "scene-handoff-contract-audit-v44.js"
    lock = "scene-handoff-stage-lock-v45.js"
    assert audit in package
    assert lock in package
    assert package.index(audit) < package.index(lock)


def test_stage_lock_forbids_survey_output_and_requires_scene():
    lock = (ROOT / "frontend/scene-handoff-stage-lock-v45.js").read_text(encoding="utf-8")
    assert "Photos → Survey is already complete" in lock
    assert "VALIDATED, ACCEPTED and IMMUTABLE INPUT" in lock
    assert "brickhouse-survey-result.json" in lock
    assert "brickhouse-scene-result.json" in lock
    assert 'schema_version="0.2"' in lock
    assert '"photos", "observations" or "known_measurements"' in lock


def test_existing_pdf_handoff_still_targets_scene_only():
    handoff = (ROOT / "frontend/scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "Ne recommence PAS le Survey" in handoff
    assert "brickhouse-scene-result.json" in handoff
    assert "ArchitecturalScene v0.2" in handoff
    assert "ARCHITECTURAL SURVEY VALIDÉ" in handoff
