from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_scene_handoff_connectivity_audit_is_loaded_after_scale_audit():
    package = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    scale = "scene-handoff-scale-audit-v48.js"
    connectivity = "scene-handoff-connectivity-audit-v49.js"
    assert scale in package
    assert connectivity in package
    assert package.index(connectivity) > package.index(scale)


def test_connectivity_audit_carries_native_stair_contract_and_retry_context():
    audit = (FRONTEND / "scene-handoff-connectivity-audit-v49.js").read_text(encoding="utf-8")
    assert "SCENE CONNECTIVITY PREFLIGHT v4.9" in audit
    assert "StairRun" in audit
    assert "0,12 m" in audit
    assert "start" in audit and "end" in audit
    assert "brickhouse.lastRejectedSceneCandidate" in audit
    assert "brickhouse.lastSceneValidationError" in audit
    assert "Ceci n'est PAS une nouvelle reconstruction depuis zéro" in audit
    assert "Survey validé" in audit
    assert "brickhouse-scene-result.json" in audit


def test_phone_shell_keeps_rejected_scene_in_step_three_and_reuses_canonical_pdf():
    loader = (FRONTEND / "photo-shell-loader.js").read_text(encoding="utf-8")
    checkpoint = (FRONTEND / "scene-correction-checkpoint.js").read_text(encoding="utf-8")
    assert "scene-correction-checkpoint.js" in loader
    assert "schema_version === '0.2'" in checkpoint
    assert "brickhouse.lastRejectedSceneCandidate" in checkpoint
    assert "brickhouse.lastSceneValidationError" in checkpoint
    assert "Créer le PDF de correction Maison" in checkpoint
    assert "download-scene-handoff" in checkpoint
    assert "[data-shell-state=\"scene\"]" in checkpoint
    assert "architecturalscene valide" in checkpoint
