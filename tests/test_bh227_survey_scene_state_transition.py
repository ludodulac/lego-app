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
    assert "primary().textContent = 'Créer le PDF Maison'" in source
    assert "event.stopImmediatePropagation()" in source
    assert "canonical.click();" in source
    assert "primary().textContent = 'Importer le JSON Maison'" in source


def test_checkpoint_bridge_cache_key_is_refreshed() -> None:
    loader = LOADER.read_text(encoding="utf-8")
    assert "photo-checkpoint-flow.js?v=checkpoint-flow-0.2-state-transition" in loader
