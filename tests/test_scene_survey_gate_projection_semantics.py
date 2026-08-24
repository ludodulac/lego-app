from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "frontend" / "scene-survey-gate.js"


def test_projection_blocker_is_not_reported_as_survey_semantic_drift() -> None:
    source = GATE.read_text(encoding="utf-8")
    assert "const surveyErrors = (surveyPayload.issues ?? []).filter(item => item.severity === 'error')" in source
    assert "if (surveyErrors.length)" in source
    assert "if (!surveyPayload.valid_for_projection && surveyPayload.projection)" in source
    assert "renderFinalSceneValidation(surveyPayload)" in source
    assert "dérive sémantique détectée" not in source


def test_real_survey_errors_include_codes_and_object_ids() -> None:
    source = GATE.read_text(encoding="utf-8")
    assert "function formatSurveyIssue(issue)" in source
    assert "issue.object_id" in source
    assert "issue.code" in source
    assert "surveyErrors.map(formatSurveyIssue)" in source
