from pathlib import Path


BASE_PROMPT = Path("frontend/brickhouse-survey-prompt.txt")
TERRAIN_AUDIT = Path("frontend/brickhouse-survey-terrain-audit-v29.txt")
PACKAGE_ENTRY = Path("frontend/brickhouse-survey-package.js")
PACKAGE_WRAPPER = Path("frontend/brickhouse-survey-package-v05.js")


def test_historical_survey_prompt_contract_is_preserved():
    text = BASE_PROMPT.read_text(encoding="utf-8")
    assert "PROMPT DE RELEVÉ ARCHITECTURAL v2.8" in text
    assert "DÉCOMPOSITION PALIER / VOLUME PORTEUR / TERRASSE" in text
    assert "AUDIT DE CONNECTIVITÉ DES STRUCTURES EXTÉRIEURES" in text
    assert "PRÉFLIGHT TOITURE MULTI-VUES" in text
    assert "attributes.physical_object_count:1" in text


def test_terrain_addendum_requires_per_facade_qualitative_audit():
    text = TERRAIN_AUDIT.read_text(encoding="utf-8")
    assert "ADDENDUM TERRAIN PHOTOS → SURVEY v2.9" in text
    assert "TERRAIN — AUDIT QUALITATIF OBLIGATOIRE" in text
    assert "PRÉFLIGHT TERRAIN — OBLIGATOIRE AVANT JSON" in text
    assert "grade_visible" in text
    assert "grade_not_supported" in text
    assert "grade_occluded" in text
    assert 'observation `kind:"terrain"`' in text
    assert "front_to_rear_up" in text
    assert "n’invente JAMAIS amplitude" in text


def test_unknown_grade_amplitude_does_not_authorize_semantic_loss():
    text = TERRAIN_AUDIT.read_text(encoding="utf-8")
    assert "Une pente certaine ne doit jamais disparaître parce que sa magnitude métrique est inconnue" in text
    assert "L'absence d'observation terrain signifie uniquement" in text
    assert "jamais que la magnitude est inconnue" in text
    assert "Aucune pente n'est inventée à partir de la seule perspective" in text


def test_pdf_handoff_actually_injects_terrain_addendum():
    entry = PACKAGE_ENTRY.read_text(encoding="utf-8")
    wrapper = PACKAGE_WRAPPER.read_text(encoding="utf-8")
    assert "brickhouse-survey-package-v05.js" in entry
    assert "pdf-handoff-0.5-terrain-audit" in entry
    assert "brickhouse-survey-package-v04.js" in wrapper
    assert "brickhouse-survey-terrain-audit-v29.txt" in wrapper
    assert "brickhouse-survey-prompt.txt" in wrapper
    assert "`${basePrompt}\\n\\n${terrainAudit}`" in wrapper
