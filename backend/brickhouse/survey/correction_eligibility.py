"""Preflight classification for SurveyAudit findings before correction generation.

This module does not apply corrections. It only answers whether a validated
finding has an automatic mutation shape supported by SurveyCorrection v0.1.
"""

from __future__ import annotations

from dataclasses import dataclass

from .audit import (
    SurveyAudit,
    SurveyAuditFinding,
    SurveyAuditSeverity,
    SurveyAuditSuggestedAction,
    SurveyAuditTargetType,
)


@dataclass(frozen=True)
class SurveyCorrectionEligibility:
    finding_id: str
    automatic: bool
    reason: str


def classify_survey_correction_finding_v01(
    finding: SurveyAuditFinding,
) -> SurveyCorrectionEligibility:
    """Classify one finding against the automatic SurveyCorrection v0.1 surface."""
    if finding.severity not in {
        SurveyAuditSeverity.WARNING,
        SurveyAuditSeverity.ERROR,
    }:
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=False,
            reason="non_actionable_severity",
        )

    action = finding.suggested_action
    target = finding.target_type

    if action in {
        SurveyAuditSuggestedAction.KEEP,
        SurveyAuditSuggestedAction.REVIEW,
    }:
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=False,
            reason="diagnostic_only_action",
        )

    if action is SurveyAuditSuggestedAction.MERGE:
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=False,
            reason="merge_requires_manual_review_v01",
        )

    if target is SurveyAuditTargetType.PHOTO:
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=False,
            reason="photo_target_not_mutable_v01",
        )

    if action is SurveyAuditSuggestedAction.ADD:
        automatic = target in {
            SurveyAuditTargetType.SURVEY,
            SurveyAuditTargetType.OBSERVATION,
            SurveyAuditTargetType.RELATION,
        }
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=automatic,
            reason="automatic_add" if automatic else "unsupported_add_target",
        )

    if action is SurveyAuditSuggestedAction.REMOVE:
        automatic = target in {
            SurveyAuditTargetType.OBSERVATION,
            SurveyAuditTargetType.RELATION,
        }
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=automatic,
            reason="automatic_remove" if automatic else "remove_requires_object_target",
        )

    if action is SurveyAuditSuggestedAction.LOWER_CERTAINTY:
        automatic = target in {
            SurveyAuditTargetType.OBSERVATION,
            SurveyAuditTargetType.RELATION,
        }
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=automatic,
            reason=(
                "automatic_lower_certainty"
                if automatic
                else "lower_certainty_requires_object_target"
            ),
        )

    if action is SurveyAuditSuggestedAction.REORIENT:
        automatic = target is SurveyAuditTargetType.OBSERVATION
        return SurveyCorrectionEligibility(
            finding_id=finding.id,
            automatic=automatic,
            reason=(
                "automatic_observation_reorient"
                if automatic
                else "reorient_requires_observation_target_v01"
            ),
        )

    return SurveyCorrectionEligibility(
        finding_id=finding.id,
        automatic=False,
        reason="unsupported_action_v01",
    )


def survey_correction_eligibility_v01(
    audit: SurveyAudit,
) -> list[SurveyCorrectionEligibility]:
    """Return deterministic correction eligibility for every finding in order."""
    return [classify_survey_correction_finding_v01(item) for item in audit.findings]


def automatic_survey_correction_finding_ids_v01(audit: SurveyAudit) -> list[str]:
    """Return only finding IDs that may be sent to automatic correction generation."""
    return [
        item.finding_id
        for item in survey_correction_eligibility_v01(audit)
        if item.automatic
    ]
