from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE_PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"
SURVEY_PROMPT = ROOT / "frontend" / "brickhouse-survey-prompt.txt"


def test_scene_prompt_separates_observed_existence_from_metric_confidence() -> None:
    source = SCENE_PROMPT.read_text(encoding="utf-8")
    assert "DISCIPLINE MÉTRIQUE" in source
    assert "existence certaine" in source
    assert "n’autorise jamais à rendre ses dimensions métriques certaines" in source
    assert "une seule largeur utilisateur" in source
    assert "ne suffit pas à déterminer automatiquement profondeur" in source


def test_scene_prompt_forbids_false_precision_and_rectangular_completion() -> None:
    source = SCENE_PROMPT.read_text(encoding="utf-8")
    assert "FAUSSE PRÉCISION" in source
    assert "rectangular_envelope" in source
    assert "enveloppe porteuse" in source
    assert "ne constitue jamais une affirmation" in source
    assert "dimensions cachées" in source


def test_scene_prompt_requires_relation_and_roof_certainty_discipline() -> None:
    scene = SCENE_PROMPT.read_text(encoding="utf-8")
    survey = SURVEY_PROMPT.read_text(encoding="utf-8")
    assert "AUTO-RELATIONS" in scene
    assert "from == to" in scene
    assert "même objet physique" in survey
    assert "ne crée pas une relation `same_physical_object` de l’objet vers lui-même" in survey
    assert "certitude de l’observation de toiture" in survey
    assert "certitude de chacun de ses attributs" in survey
