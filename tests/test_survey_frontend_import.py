from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_photo_page_uses_survey_import_without_legacy_photo_analyzer() -> None:
    html = read("photo.html")
    survey_pos = html.index('./survey-import.js')
    scene_pos = html.index('./scene-handoff-photo-evidence.js')
    assert survey_pos < scene_pos
    assert './photo.js' not in html
    assert './photo-capture-runtime.js' in html


def test_survey_import_routes_to_validate_survey_and_never_builds_directly() -> None:
    script = read("survey-import.js")
    assert "/api/v1/validate-survey" in script
    assert "isArchitecturalSurvey" in script
    assert "valid_for_scene_fusion" in script
    assert "surveyBuild.disabled = true" in script
    assert "stopImmediatePropagation" in script


def test_survey_import_persists_validated_survey_for_next_stage() -> None:
    script = read("survey-import.js")
    assert "brickhouse.pendingArchitecturalSurvey" in script
    assert "ArchitecturalSurvey valide" in script
