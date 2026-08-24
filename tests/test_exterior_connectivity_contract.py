from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_survey_requires_explicit_exterior_connectivity_relations() -> None:
    prompt = (FRONTEND / "brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "PROMPT DE RELEVÉ ARCHITECTURAL v2.7" in prompt
    assert "AUDIT DE CONNECTIVITÉ DES STRUCTURES EXTÉRIEURES" in prompt
    assert "ajoute une relation `connects_to` vers l’observation `building_boundary`" in prompt
    assert "toute primitive extérieure certaine" in prompt


def test_scene_preserves_unresolved_survey_semantic_anchors() -> None:
    prompt = (FRONTEND / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")
    assert "PROMPT DE RECONSTRUCTION SURVEY → SCENE v3.6" in prompt
    assert "notamment `building_boundary`" in prompt
    assert "au moins un endpoint d’une relation `unresolved` doit être un objet Scene présent" in prompt
    assert "relation certaine vers `building_boundary`" in prompt
