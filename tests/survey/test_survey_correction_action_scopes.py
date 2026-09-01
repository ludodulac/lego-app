from __future__ import annotations

import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey, SurveyAudit, SurveyCorrection, validate_survey_correction


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _audit(
    survey: ArchitecturalSurvey,
    *,
    finding_id: str,
    target_id: str,
    action: str,
) -> SurveyAudit:
    return SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": survey.id,
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": finding_id,
                    "status": "disputed",
                    "target_type": "observation",
                    "target_id": target_id,
                    "severity": "warning",
                    "photo_evidence": [
                        {"photo_index": 1, "observation": "Target visible in the source photo."}
                    ],
                    "message": "Audit-linked correction required.",
                    "suggested_action": action,
                }
            ],
        }
    )


def _correction(
    survey: ArchitecturalSurvey,
    audit: SurveyAudit,
    candidate: ArchitecturalSurvey,
    *,
    change_id: str,
    target_id: str,
    action: str,
    candidate_id: str | None = None,
) -> SurveyCorrection:
    return SurveyCorrection.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_correction",
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": change_id,
                    "finding_id": audit.findings[0].id,
                    "object_type": "observation",
                    "source_id": target_id,
                    "candidate_id": candidate_id if candidate_id is not None else target_id,
                    "action": action,
                    "message": "Apply only the audited action.",
                }
            ],
        }
    )


def test_lower_certainty_accepts_only_a_real_certainty_decrease() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.certainty = "plausible"
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )

    assert validate_survey_correction(survey, audit, correction) == []


def test_lower_certainty_rejects_semantic_mutation_hidden_in_same_change() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.certainty = "plausible"
    target.attributes["semantic_type"] = "door"
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_lower_certainty_scope_violation" in codes


def test_reorient_accepts_facade_rank_change_without_semantic_rewrite() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-reorient-window",
        target_id=target_id,
        action="reorient",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.attributes["facade_horizontal_rank"] = 3
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-reorient-window",
        target_id=target_id,
        action="reorient",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert not {code for code in codes if code.startswith("survey_correction_reorient_")}


def test_reorient_rejects_non_orientation_attribute_change() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-reorient-window",
        target_id=target_id,
        action="reorient",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.attributes["facade_horizontal_rank"] = 3
    target.attributes["semantic_type"] = "door"
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-reorient-window",
        target_id=target_id,
        action="reorient",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_reorient_non_orientation_attribute_changed" in codes


def test_merge_remains_manual_review_only_in_v01() -> None:
    survey = _survey()
    source_id = "front_upper_left_window"
    target_id = "front_upper_right_window"
    audit = _audit(
        survey,
        finding_id="audit-duplicate-window",
        target_id=source_id,
        action="merge",
    )
    candidate = survey.model_copy(deep=True)
    candidate.observations = [item for item in candidate.observations if item.id != source_id]
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-merge-window",
        target_id=source_id,
        candidate_id=target_id,
        action="merge",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_merge_requires_manual_review" in codes
