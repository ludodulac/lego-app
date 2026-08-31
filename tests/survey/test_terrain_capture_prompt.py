from pathlib import Path


PROMPT = Path("frontend/brickhouse-survey-prompt.txt")


def test_survey_prompt_requires_per_facade_terrain_audit():
    text = PROMPT.read_text(encoding="utf-8")
    assert "PROMPT DE RELEVÉ ARCHITECTURAL v2.9" in text
    assert "TERRAIN — AUDIT QUALITATIF OBLIGATOIRE" in text
    assert "PRÉFLIGHT TERRAIN — OBLIGATOIRE AVANT JSON" in text
    assert "grade_visible" in text
    assert "grade_not_supported" in text
    assert "grade_occluded" in text
    assert 'observation `kind:"terrain"`' in text
    assert "front_to_rear_up" in text
    assert "n’invente JAMAIS amplitude" in text


def test_unknown_grade_amplitude_does_not_authorize_semantic_loss():
    text = PROMPT.read_text(encoding="utf-8")
    assert "Une pente certaine ne doit jamais disparaître parce que sa magnitude métrique est inconnue" in text
    assert "l’absence d’observation terrain signifie uniquement" in text
    assert "jamais que la magnitude est inconnue" in text
    assert "aucune pente n’est inventée à partir de la seule perspective" in text
