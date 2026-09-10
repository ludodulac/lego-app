from pathlib import Path


GUARD = Path("frontend/scene-import-routing-guard.js")
ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_scene_import_without_active_survey_is_not_fed_to_survey_importer():
    text = GUARD.read_text(encoding="utf-8")

    assert "schema_version === '0.2'" in text
    assert "brickhouse.pendingArchitecturalSurvey" in text
    assert "event.stopImmediatePropagation()" in text
    assert "ArchitecturalScene v0.2 reconnue" in text
    assert "la Scene n’a pas été interprétée comme un relevé" in text


def test_scene_import_routing_guard_is_loaded_before_separate_survey_import_script():
    text = ENTRY.read_text(encoding="utf-8")

    assert "scene-import-routing-guard.js" in text
    assert "real-house-5" not in GUARD.read_text(encoding="utf-8")
