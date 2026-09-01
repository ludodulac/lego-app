from __future__ import annotations

from brickhouse.survey import SurveyAudit
from brickhouse.survey.correction_eligibility import (
    automatic_survey_correction_finding_ids_v01,
    survey_correction_eligibility_v01,
)


def _audit() -> SurveyAudit:
    findings = [
        ("missing-roof", "missing", "survey", None, "error", "add"),
        ("remove-relation", "disputed", "relation", "relation-1", "warning", "remove"),
        ("lower-opening", "disputed", "observation", "opening-1", "warning", "lower_certainty"),
        ("reorient-opening", "disputed", "observation", "opening-2", "warning", "reorient"),
        ("reorient-relation", "disputed", "relation", "relation-2", "warning", "reorient"),
        ("merge-opening", "duplicate", "observation", "opening-3", "warning", "merge"),
        ("review-opening", "insufficient_evidence", "observation", "opening-4", "warning", "review"),
        ("photo-problem", "disputed", "photo", "1", "warning", "remove"),
        ("info-only", "confirmed", "observation", "opening-5", "info", "remove"),
    ]
    return SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": "survey",
            "summary": {"status": "needs_correction", "issue_count": len(findings)},
            "findings": [
                {
                    "id": finding_id,
                    "status": status,
                    "target_type": target_type,
                    "target_id": target_id,
                    "severity": severity,
                    "photo_evidence": (
                        []
                        if status == "insufficient_evidence"
                        else [{"photo_index": 1, "observation": "Visible evidence."}]
                    ),
                    "message": "Test finding.",
                    "suggested_action": action,
                }
                for finding_id, status, target_type, target_id, severity, action in findings
            ],
        }
    )


def test_eligibility_preflight_matches_hardened_v01_surface() -> None:
    audit = _audit()

    assert automatic_survey_correction_finding_ids_v01(audit) == [
        "missing-roof",
        "remove-relation",
        "lower-opening",
        "reorient-opening",
    ]

    by_id = {item.finding_id: item for item in survey_correction_eligibility_v01(audit)}
    assert by_id["reorient-relation"].reason == "reorient_requires_observation_target_v01"
    assert by_id["merge-opening"].reason == "merge_requires_manual_review_v01"
    assert by_id["review-opening"].reason == "diagnostic_only_action"
    assert by_id["photo-problem"].reason == "photo_target_not_mutable_v01"
    assert by_id["info-only"].reason == "non_actionable_severity"
