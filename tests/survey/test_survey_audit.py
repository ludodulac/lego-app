from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.survey import ArchitecturalSurvey, SurveyAudit, validate_survey_audit


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"
PROMPT = Path(__file__).parents[2] / "frontend" / "brickhouse-survey-independent-audit-v01.txt"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _audit_payload(survey: ArchitecturalSurvey) -> dict:
    return {
        "schema_version": "0.1",
        "kind": "survey_audit",
        "survey_id": survey.id,
        "summary": {"status": "needs_correction", "issue_count": 1},
        "findings": [
            {
                "id": "audit-terrain-certainty",
                "status": "disputed",
                "target_type": "observation",
                "target_id": "right_rising_road",
                "severity": "warning",
                "photo_evidence": [
                    {
                        "photo_index": 1,
                        "observation": "The visible grade direction is weaker than the Survey certainty claims.",
                    }
                ],
                "message": "The claim should be reviewed against the source pixels.",
                "suggested_action": "lower_certainty",
            }
        ],
    }


def test_survey_audit_accepts_diagnostic_finding_without_mutating_survey():
    survey = _survey()
    original = survey.model_dump(mode="json")
    audit = SurveyAudit.model_validate(_audit_payload(survey))

    assert validate_survey_audit(survey, audit) == []
    assert survey.model_dump(mode="json") == original
    assert audit.kind == "survey_audit"
    assert audit.schema_version == "0.1"


def test_survey_audit_requires_photo_evidence_for_non_insufficient_findings():
    survey = _survey()
    payload = _audit_payload(survey)
    payload["findings"][0]["photo_evidence"] = []

    with pytest.raises(ValidationError, match="must cite photo_evidence"):
        SurveyAudit.model_validate(payload)


def test_survey_audit_allows_insufficient_evidence_without_photo_claim():
    survey = _survey()
    payload = _audit_payload(survey)
    payload["summary"] = {"status": "pass", "issue_count": 1}
    payload["findings"][0].update(
        status="insufficient_evidence",
        severity="info",
        photo_evidence=[],
        suggested_action="review",
    )
    audit = SurveyAudit.model_validate(payload)

    assert validate_survey_audit(survey, audit) == []


def test_survey_audit_rejects_unknown_photo_and_target_semantically():
    survey = _survey()
    payload = _audit_payload(survey)
    payload["findings"][0]["target_id"] = "missing-observation"
    payload["findings"][0]["photo_evidence"][0]["photo_index"] = 999
    audit = SurveyAudit.model_validate(payload)

    codes = {issue.code for issue in validate_survey_audit(survey, audit)}
    assert "survey_audit_unknown_photo" in codes
    assert "survey_audit_unknown_observation" in codes


def test_survey_audit_summary_status_tracks_actionable_findings():
    survey = _survey()
    payload = _audit_payload(survey)
    payload["summary"]["status"] = "pass"
    audit = SurveyAudit.model_validate(payload)

    codes = {issue.code for issue in validate_survey_audit(survey, audit)}
    assert "survey_audit_summary_status_mismatch" in codes


def test_survey_audit_issue_count_is_exact():
    survey = _survey()
    payload = _audit_payload(survey)
    payload["summary"]["issue_count"] = 0

    with pytest.raises(ValidationError, match="issue_count"):
        SurveyAudit.model_validate(payload)


def test_survey_audit_json_schema_is_versioned_and_separate():
    schema = SurveyAudit.model_json_schema()

    assert schema["properties"]["schema_version"]["const"] == "0.1"
    assert schema["properties"]["kind"]["const"] == "survey_audit"
    assert "ArchitecturalSurvey" not in schema.get("$defs", {})


def test_independent_audit_prompt_is_diagnostic_only():
    text = PROMPT.read_text(encoding="utf-8")

    assert "Return only one SurveyAudit v0.1 JSON object" in text
    assert "Never return a corrected ArchitecturalSurvey" in text
    assert "Absence of evidence is not proof of absence" in text
    assert "deterministic" in text
