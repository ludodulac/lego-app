from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "frontend" / "scene-survey-gate.js"


def test_scene_import_hydrates_missing_certain_survey_relations() -> None:
    source = GATE.read_text(encoding="utf-8")
    assert "function hydrateCertainSurveyRelations" in source
    assert "relation?.certainty !== 'certain'" in source
    assert "geometry_status: 'unresolved'" in source
    assert "parsed = hydrateCertainSurveyRelations(survey, parsed);" in source
    assert "objectIds.has(relation.subject_id)" in source
    assert "objectIds.has(relation.object_id)" in source


def test_scene_relation_hydration_never_invents_unknown_endpoints() -> None:
    source = GATE.read_text(encoding="utf-8")
    assert "if (!objectIds.has(relation.subject_id) || !objectIds.has(relation.object_id)) continue;" in source
    assert "existingIds.has(relation.id)" in source
