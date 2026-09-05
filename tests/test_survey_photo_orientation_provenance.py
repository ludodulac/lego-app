from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_orientation_provenance_audit_preserves_capture_hints_without_promoting_them():
    audit = (FRONTEND / "brickhouse-survey-orientation-provenance-audit-v36.txt").read_text(encoding="utf-8")
    assert "capture_hint" in audit
    assert "conserve donc `facade` exactement égal à la case fournie" in audit
    assert "ne peut pas l’écraser" in audit
    assert "n’élève pas ce hint à `user_confirmed`" in audit
    assert "targeted_detail" in audit and "facade:null" in audit
    assert "front, right, left, left, rear" in audit


def test_orientation_provenance_prompt_layer_is_wired_after_measurement_provenance():
    entry = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    measurement = "brickhouse-survey-package-v09.js?v=pdf-handoff-0.9-measurement-provenance"
    orientation = "brickhouse-survey-package-v11.js?v=pdf-handoff-0.11-orientation-provenance"
    gate = "survey-photo-orientation-provenance-gate.js?v=orientation-provenance-gate-0.1"
    assert measurement in entry
    assert orientation in entry
    assert gate in entry
    assert entry.index(measurement) < entry.index(orientation) < entry.index(gate)


def test_import_gate_reconstructs_capture_order_and_rejects_silent_facade_permutations():
    gate = (FRONTEND / "survey-photo-orientation-provenance-gate.js").read_text(encoding="utf-8")
    assert "const SLOT_ORDER = ['front', 'right', 'left', 'rear'];" in gate
    assert "currentCapturePhotoContract" in gate
    assert ".guided-photo-slot" in gate
    assert ".detail-photo-slot" in gate
    assert "actual.length !== expected.length" in gate
    assert "Number(actualPhoto?.photo_index) !== expectedIndex" in gate
    assert "actualPhoto?.capture_role !== expectedPhoto.capture_role" in gate
    assert "actualPhoto?.facade ?? null" in gate
    assert "Orientation refusée" in gate
    assert "Une contradiction visuelle doit être conservée en note" in gate
    assert "event.stopImmediatePropagation()" in gate
