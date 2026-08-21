from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_photo_page_loads_survey_import_before_legacy_importer() -> None:
    html = read("photo.html")
    survey_pos = html.index('./survey-import.js')
    photo_pos = html.index('./photo.js')
    assert survey_pos < photo_pos


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
