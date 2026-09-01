from pathlib import Path


SOURCE_LOCK = Path("frontend/scene-handoff-source-lock.js")
PACKAGE_ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_scene_handoff_source_lock_is_loaded_from_stable_photo_entrypoint():
    entry = PACKAGE_ENTRY.read_text(encoding="utf-8")
    assert "scene-handoff-source-lock.js" in entry
    assert "scene-handoff-source-lock-0.1" in entry


def test_source_lock_manifest_preserves_active_survey_semantics():
    text = SOURCE_LOCK.read_text(encoding="utf-8")
    assert "VERROU SOURCE SURVEY → SCENE" in text
    assert "active_terrain" in text
    assert "active_roofs" in text
    assert "building_boundary_ids" in text
    assert "terrain.profiles contient un profil de la même façade" in text
    assert 'facade_is_gable:true certain/plausible ne doit pas devenir type:\"other\"' in text
    assert "n'invente jamais obs-building-envelope" in text
    assert "compare le JSON Scene final à ce manifeste" in text


def test_new_survey_import_invalidates_previous_scene_handoff_before_validation():
    text = SOURCE_LOCK.read_text(encoding="utf-8")
    assert "clearStaleSurveyHandoff" in text
    assert "localStorage.removeItem(PENDING_SURVEY_KEY)" in text
    assert "#scene-handoff-home" in text
    assert "#import-analysis" in text
    assert "schema_version === '0.1'" in text
