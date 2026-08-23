from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE_PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"
SURVEY_PROMPT = ROOT / "frontend" / "brickhouse-survey-prompt.txt"
TOPOLOGY_PROMPT = ROOT / "frontend" / "brickhouse-topology-prompt.txt"


def test_scene_prompt_separates_observed_existence_from_metric_confidence() -> None:
    source = SCENE_PROMPT.read_text(encoding="utf-8")
    assert "DISCIPLINE MÉTRIQUE" in source
    assert "Une existence certaine n’autorise jamais à rendre ses dimensions métriques certaines" in source
    assert "Une seule largeur utilisateur ne suffit pas" in source
    assert "source.kind=\"inferred\"" in source
    assert "FAUSSE PRÉCISION" in source


def test_scene_prompt_is_locked_to_backend_v02_shapes() -> None:
    source = SCENE_PROMPT.read_text(encoding="utf-8")
    assert "SURVEY → SCENE v2.7" in source
    assert 'schema_version` DOIT valoir exactement `"0.2"' in source
    assert "Position3D est TOUJOURS un objet" in source
    assert "PropertyValue" in source
    assert "SceneVolume" in source
    assert "SupportPost" in source
    assert 'type:"other"' in source
    assert "facade_grade_profiles" in source
    assert "building_boundary" in source


def test_survey_prompt_is_locked_to_backend_v01_shapes() -> None:
    source = SURVEY_PROMPT.read_text(encoding="utf-8")
    assert "RELEVÉ ARCHITECTURAL v2.1" in source
    assert 'schema_version` DOIT valoir exactement `"0.1"' in source
    assert '"kind":"front_width"' in source
    assert "subject_id" in source
    assert "object_id" in source
    assert "same_physical_object" in source
    assert "certitude de l’observation de toiture" in source


def test_topology_prompt_obeys_single_turn_and_treats_slot_labels_as_hints() -> None:
    source = TOPOLOGY_PROMPT.read_text(encoding="utf-8")
    assert "TOPOLOGIQUE v0.6" in source
    assert "execution_mode=single_turn_file_output" in source
    assert "N’ENTRE PAS en mode conversationnel" in source
    assert "REPÈRE DE CAPTURE" in source
    assert "indices faibles" in source
    assert "user_confirmed" in source
