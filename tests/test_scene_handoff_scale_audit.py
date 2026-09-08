from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCALE_AUDIT = ROOT / "frontend" / "scene-handoff-scale-audit-v48.js"
PACKAGE = ROOT / "frontend" / "brickhouse-survey-package.js"


def test_measurement_free_scale_audit_requires_multi_cue_consensus() -> None:
    text = SCALE_AUDIT.read_text(encoding="utf-8")

    assert "MEASUREMENT-FREE SCALE AUDIT v4.8" in text
    assert "known_measurements:[]" in text
    assert "Une seule fenêtre" in text
    assert 'source.kind=\"inferred\"' in text
    assert "value:null" in text
    assert "user_provided" in text
    assert "au moins deux familles" in text
    assert "absence de mesure utilisateur" in text


def test_scale_audit_does_not_hardcode_benchmark_or_regional_sizes() -> None:
    text = SCALE_AUDIT.read_text(encoding="utf-8")

    assert "real-house-5" not in text
    assert "France" not in text
    assert "Europe" not in text
    assert "10.0" not in text
    assert "2.15" not in text


def test_scale_audit_is_wired_after_ownership_audit() -> None:
    text = PACKAGE.read_text(encoding="utf-8")

    assert text.index("scene-handoff-ownership-audit-v47.js") < text.index(
        "scene-handoff-scale-audit-v48.js"
    )
