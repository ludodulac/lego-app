from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPORT = ROOT / "frontend" / "scene-result-import.js"


def test_scene_import_has_hard_architectural_readiness_gate() -> None:
    text = IMPORT.read_text(encoding="utf-8")
    assert "function architecturalReadiness" in text
    assert "projectionBlockers" in text
    assert "requiredInputs" in text
    assert "compatibilityBlockers" in text
    assert "buildButton.disabled = !architecturalReady" in text
    assert "if (!acceptedScene || !surveyValidation || !architecturalReady) return;" in text


def test_scene_import_no_longer_falls_back_to_partial_lego_build() -> None:
    text = IMPORT.read_text(encoding="utf-8")
    assert "allow_partial: false" in text
    assert "allow_partial: true" not in text
    assert "briques fiables" not in text
    assert "LEGO bloqué — Scene à résoudre" in text


def test_readiness_is_persisted_with_scene_handoff() -> None:
    text = IMPORT.read_text(encoding="utf-8")
    assert "architectural_readiness: readiness" in text
    assert "Maturité architecturale insuffisante" in text
