from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_measurement_provenance_audit_forbids_fabricated_user_measurements():
    audit = (FRONTEND / "brickhouse-survey-measurement-provenance-audit-v35.txt").read_text()
    assert 'source.kind:"user_provided"' in audit
    assert "known_front_width_m:null" in audit
    assert "zéro mesure `front_width`" in audit
    assert "même valeur numérique" in audit
    assert "mêmes unités" in audit


def test_v09_layers_provenance_audit_after_existing_survey_audits():
    package = (FRONTEND / "brickhouse-survey-package-v09.js").read_text()
    assert "brickhouse-survey-package-v08.js" in package
    assert "brickhouse-survey-measurement-provenance-audit-v35.txt" in package
    assert "measurementProvenanceAwareSurveyFetch" in package
    assert "`${promptWithExistingAudits}\\n\\n${measurementAudit}`" in package


def test_import_gate_rejects_absent_mismatched_and_unsupported_user_measurements():
    gate = (FRONTEND / "survey-measurement-provenance-gate.js").read_text()
    assert "measurement.kind !== 'front_width'" in gate
    assert "authorizedFrontWidth === null" in gate
    assert "measurement.units !== 'm'" in gate
    assert "Math.abs(value - authorizedFrontWidth) > 1e-9" in gate
    assert "event.stopImmediatePropagation()" in gate
    assert "aucune Scene ne sera préparée" in gate


def test_import_gate_allows_only_exact_current_front_width_authority():
    gate = (FRONTEND / "survey-measurement-provenance-gate.js").read_text()
    assert "const authorizedFrontWidth = explicitFrontWidth();" in gate
    assert "Number(knownWidthInput?.value)" in gate
    assert "measurement.kind !== 'front_width'" in gate
    assert "measurement.units !== 'm'" in gate


def test_stable_entrypoint_loads_prompt_and_runtime_provenance_locks():
    stable = (FRONTEND / "brickhouse-survey-package.js").read_text()
    v09 = stable.index("brickhouse-survey-package-v09.js")
    gate = stable.index("survey-measurement-provenance-gate.js")
    source_lock = stable.index("scene-handoff-source-lock.js")
    benchmark = stable.index("real-house-benchmark-loader.js")
    assert v09 < gate < source_lock < benchmark
