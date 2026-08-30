from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_prompt_requires_reasoning_before_json() -> None:
    text = PROMPT.read_text(encoding="utf-8")
    assert "PROMPT DE RECONSTRUCTION SURVEY → SCENE v4.2" in text
    assert "PASSE DE RAISONNEMENT ARCHITECTURAL — OBLIGATOIRE AVANT TOUT JSON" in text
    assert "IDENTITÉ MULTI-VUES" in text
    assert "COMPRÉHENSION ARCHITECTURALE" in text
    assert "HYPOTHÈSES AVANT VALEURS" in text
    assert "RÉSOLUTION CONJOINTE" in text
    assert "CONTRADICTION ACTIVE" in text
    assert "TEST NUMÉRIQUE FINAL" in text


def test_stair_reasoning_is_architectural_not_just_validator_driven() -> None:
    text = PROMPT.read_text(encoding="utf-8")
    assert "sens de montée" in text
    assert "l’extrémité basse" in text
    assert "l’extrémité haute" in text
    assert "surface ou le volume reçu à l’arrivée" in text
    assert "marches/contremarches/murs latéraux" in text
    assert "INTERDIT d’estimer séparément deux objets" in text
    assert "relation n’est `resolved` qu’après ce test numérique" in text


def test_reference_object_priors_are_bounded_secondary_evidence() -> None:
    text = PROMPT.read_text(encoding="utf-8")
    assert "référence dimensionnelle usuelle" in text
    assert "plage secondaire plausible" in text
    assert "ne remplace jamais les preuves propres au bâtiment" in text
