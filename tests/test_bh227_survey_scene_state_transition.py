from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "frontend" / "photo-checkpoint-flow.js"
LOADER = ROOT / "frontend" / "photo-shell-loader.js"


def test_validated_survey_advances_to_maison_and_owns_single_primary_action() -> None:
    source = FLOW.read_text(encoding="utf-8")
    assert "surveyIsValidated()" in source
    assert "autoAdvancedSurveyId !== id" in source
    assert "goToScene();" in source
    assert "document.querySelector('#shell-survey-next')?.remove()" in source
    assert "setPrimaryLabel('Créer le PDF Maison')" in source
    assert "event.stopImmediatePropagation()" in source
    assert "canonical.click();" in source
    assert "setPrimaryLabel('Importer le JSON Maison')" in source


def test_checkpoint_observer_dom_writes_are_idempotent() -> None:
    source = FLOW.read_text(encoding="utf-8")
    assert "if (node && node.textContent !== value) node.textContent = value" in source
    assert "setText(document.querySelector('#shell-scene-status'), message)" in source
    assert "setText(primary(), message)" in source


def test_checkpoint_bridge_cache_key_is_refreshed() -> None:
    loader = LOADER.read_text(encoding="utf-8")
    assert "photo-checkpoint-flow.js?v=checkpoint-flow-0.3-idempotent-observer" in loader
