from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
AUDIT = FRONTEND / "scene-handoff-contract-audit-v44.js"
PACKAGE = FRONTEND / "brickhouse-survey-package.js"


def test_generated_handoff_receives_backend_resolved_contact_rule_from_v44_audit() -> None:
    generator = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    package = PACKAGE.read_text(encoding="utf-8")
    assert "${prompt}" in generator
    assert "scene-handoff-contract-audit-v44.js" in package
    assert "FINAL RESOLVED-CONTACT AUDIT" in audit
    assert "0.12 m" in audit
    assert "StairRun endpoint contact" in audit
    assert "stair width never counts as contact" in audit
    assert "semantic_anchor_volume_id" in audit
    assert 'geometry_status="resolved"' in audit


def test_resolved_contact_guard_does_not_snap_imported_geometry() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "snapResolved" not in source
    assert "snapToVolume" not in source
    assert "stair.start =" not in source
    assert "stair.end =" not in source
