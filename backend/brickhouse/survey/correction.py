"""Explicit, audit-linked correction contract for ArchitecturalSurvey.

A SurveyCorrection never patches a Survey implicitly. It carries a complete
candidate Survey plus a journal tying every model-level observation/relation
change to one actionable SurveyAudit finding.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .audit import (
    SurveyAudit,
    SurveyAuditSeverity,
    SurveyAuditStatus,
    SurveyAuditSuggestedAction,
    SurveyAuditTargetType,
)
from .models import ArchitecturalSurvey, Certainty, SurveyObservation, SurveyRelation
from .roof_guard import validate_multiview_roof_hypotheses
from .validation import validate_survey_semantics


class SurveyCorrectionObjectType(str, Enum):
    OBSERVATION = "observation"
    RELATION = "relation"


class SurveyCorrectionChange(BaseModel):
    id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    object_type: SurveyCorrectionObjectType
    source_id: str | None = None
    candidate_id: str | None = None
    action: SurveyAuditSuggestedAction
    message: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ids_for_action(self) -> "SurveyCorrectionChange":
        if self.action is SurveyAuditSuggestedAction.ADD:
            if self.source_id is not None or not self.candidate_id:
                raise ValueError("add corrections require candidate_id and no source_id")
        elif self.action is SurveyAuditSuggestedAction.REMOVE:
            if not self.source_id or self.candidate_id is not None:
                raise ValueError("remove corrections require source_id and no candidate_id")
        elif self.action in {
            SurveyAuditSuggestedAction.LOWER_CERTAINTY,
            SurveyAuditSuggestedAction.REORIENT,
        }:
            if not self.source_id or self.candidate_id != self.source_id:
                raise ValueError(
                    "in-place corrections require source_id == candidate_id"
                )
        elif self.action is SurveyAuditSuggestedAction.MERGE:
            if not self.source_id or not self.candidate_id:
                raise ValueError("merge corrections require source_id and candidate_id")
        elif self.action in {
            SurveyAuditSuggestedAction.KEEP,
            SurveyAuditSuggestedAction.REVIEW,
        }:
            raise ValueError(
                "keep/review findings are diagnostic and cannot directly mutate a Survey"
            )
        return self


class SurveyCorrection(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    kind: Literal["survey_correction"] = "survey_correction"
    survey_id: str = Field(min_length=1)
    candidate: ArchitecturalSurvey
    changes: list[SurveyCorrectionChange] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_change_ids(self) -> "SurveyCorrection":
        ids = [change.id for change in self.changes]
        if len(ids) != len(set(ids)):
            raise ValueError("SurveyCorrection change ids must be unique")
        return self


@dataclass(frozen=True)
class SurveyCorrectionValidationIssue:
    code: str
    change_id: str | None
    message: str
    severity: str = "error"


_CERTAINTY_RANK = {
    Certainty.UNPROVEN: 0,
    Certainty.PLAUSIBLE: 1,
    Certainty.CERTAIN: 2,
}
_ORIENTATION_ATTRIBUTE_KEYS = {
    "facade_horizontal_rank",
    "facade_vertical_rank",
}


def _maps(survey: ArchitecturalSurvey):
    return (
        {item.id: item for item in survey.observations},
        {item.id: item for item in survey.relations},
    )


def _diff_ids(before: dict, after: dict) -> tuple[set[str], set[str], set[str]]:
    before_ids = set(before)
    after_ids = set(after)
    added = after_ids - before_ids
    removed = before_ids - after_ids
    modified = {
        item_id
        for item_id in before_ids & after_ids
        if before[item_id] != after[item_id]
    }
    return added, removed, modified


def _validation_issue(
    code: str,
    change: SurveyCorrectionChange,
    message: str,
) -> SurveyCorrectionValidationIssue:
    return SurveyCorrectionValidationIssue(
        code=code,
        change_id=change.id,
        message=message,
    )


def _validate_lower_certainty_scope(
    change: SurveyCorrectionChange,
    before: SurveyObservation | SurveyRelation,
    after: SurveyObservation | SurveyRelation,
) -> list[SurveyCorrectionValidationIssue]:
    issues: list[SurveyCorrectionValidationIssue] = []

    if isinstance(before, SurveyObservation) and isinstance(after, SurveyObservation):
        frozen_fields = (
            "id",
            "kind",
            "facade",
            "statement",
            "evidence",
            "attributes",
            "appearance",
            "opening_visual",
        )
        if any(getattr(before, field) != getattr(after, field) for field in frozen_fields):
            issues.append(
                _validation_issue(
                    "survey_correction_lower_certainty_scope_violation",
                    change,
                    "lower_certainty may change only object/attribute certainty, not observation content.",
                )
            )

        increased = _CERTAINTY_RANK[after.certainty] > _CERTAINTY_RANK[before.certainty]
        decreased = _CERTAINTY_RANK[after.certainty] < _CERTAINTY_RANK[before.certainty]
        for name in before.attributes:
            before_level = before.certainty_for_attribute(name)
            after_level = after.certainty_for_attribute(name)
            increased = increased or _CERTAINTY_RANK[after_level] > _CERTAINTY_RANK[before_level]
            decreased = decreased or _CERTAINTY_RANK[after_level] < _CERTAINTY_RANK[before_level]
        if increased:
            issues.append(
                _validation_issue(
                    "survey_correction_lower_certainty_increased_certainty",
                    change,
                    "lower_certainty cannot increase object or attribute certainty.",
                )
            )
        if not decreased:
            issues.append(
                _validation_issue(
                    "survey_correction_lower_certainty_no_decrease",
                    change,
                    "lower_certainty must strictly lower at least one effective certainty value.",
                )
            )
        return issues

    if isinstance(before, SurveyRelation) and isinstance(after, SurveyRelation):
        frozen_fields = ("id", "kind", "subject_id", "object_id", "statement", "evidence")
        if any(getattr(before, field) != getattr(after, field) for field in frozen_fields):
            issues.append(
                _validation_issue(
                    "survey_correction_lower_certainty_scope_violation",
                    change,
                    "lower_certainty may change only relation certainty, not relation content.",
                )
            )
        if _CERTAINTY_RANK[after.certainty] >= _CERTAINTY_RANK[before.certainty]:
            issues.append(
                _validation_issue(
                    "survey_correction_lower_certainty_no_decrease",
                    change,
                    "lower_certainty must strictly lower relation certainty.",
                )
            )
        return issues

    return [
        _validation_issue(
            "survey_correction_lower_certainty_type_mismatch",
            change,
            "lower_certainty source and candidate must preserve the object type.",
        )
    ]


def _validate_reorient_scope(
    change: SurveyCorrectionChange,
    before: SurveyObservation | SurveyRelation,
    after: SurveyObservation | SurveyRelation,
) -> list[SurveyCorrectionValidationIssue]:
    if not isinstance(before, SurveyObservation) or not isinstance(after, SurveyObservation):
        return [
            _validation_issue(
                "survey_correction_reorient_relation_unsupported",
                change,
                "SurveyCorrection v0.1 reorient is limited to observations; relation reorientation requires manual review.",
            )
        ]

    issues: list[SurveyCorrectionValidationIssue] = []
    frozen_fields = (
        "id",
        "kind",
        "certainty",
        "evidence",
        "attribute_certainty",
        "appearance",
        "opening_visual",
    )
    if any(getattr(before, field) != getattr(after, field) for field in frozen_fields):
        issues.append(
            _validation_issue(
                "survey_correction_reorient_scope_violation",
                change,
                "reorient cannot change identity, kind, certainty, evidence, or visual/material detail.",
            )
        )

    before_non_orientation = {
        key: value
        for key, value in before.attributes.items()
        if key not in _ORIENTATION_ATTRIBUTE_KEYS
    }
    after_non_orientation = {
        key: value
        for key, value in after.attributes.items()
        if key not in _ORIENTATION_ATTRIBUTE_KEYS
    }
    if before_non_orientation != after_non_orientation:
        issues.append(
            _validation_issue(
                "survey_correction_reorient_non_orientation_attribute_changed",
                change,
                "reorient may change only facade and facade rank attributes.",
            )
        )

    orientation_changed = before.facade != after.facade or any(
        before.attributes.get(key) != after.attributes.get(key)
        for key in _ORIENTATION_ATTRIBUTE_KEYS
    )
    if not orientation_changed:
        issues.append(
            _validation_issue(
                "survey_correction_reorient_no_orientation_change",
                change,
                "reorient must actually change facade or facade rank orientation data.",
            )
        )
    return issues


def validate_survey_correction(
    original: ArchitecturalSurvey,
    audit: SurveyAudit,
    correction: SurveyCorrection,
) -> list[SurveyCorrectionValidationIssue]:
    """Validate one explicit correction candidate against its source audit.

    v0.1 deliberately freezes non-observation Survey truth. This keeps exact
    user measurements, photo metadata, frame, representation policy and document
    identity outside the automatic correction surface while the workflow is
    experimental.
    """
    issues: list[SurveyCorrectionValidationIssue] = []
    candidate = correction.candidate

    if correction.survey_id != original.id or candidate.id != original.id:
        issues.append(
            SurveyCorrectionValidationIssue(
                code="survey_correction_id_mismatch",
                change_id=None,
                message="Correction and candidate must preserve the original Survey id.",
            )
        )
    if audit.survey_id != original.id:
        issues.append(
            SurveyCorrectionValidationIssue(
                code="survey_correction_audit_id_mismatch",
                change_id=None,
                message="SurveyAudit must refer to the original Survey id.",
            )
        )
    if audit.summary.status is not SurveyAuditStatus.NEEDS_CORRECTION:
        issues.append(
            SurveyCorrectionValidationIssue(
                code="survey_correction_without_actionable_audit",
                change_id=None,
                message="A correction requires SurveyAudit status needs_correction.",
            )
        )

    frozen_fields = (
        "name",
        "canonical_frame",
        "photos",
        "known_measurements",
        "representation_policy",
        "notes",
    )
    for field in frozen_fields:
        if getattr(candidate, field) != getattr(original, field):
            issues.append(
                SurveyCorrectionValidationIssue(
                    code=f"survey_correction_frozen_{field}_changed",
                    change_id=None,
                    message=(
                        f"SurveyCorrection v0.1 cannot change {field}; "
                        "only observations and relations are in scope."
                    ),
                )
            )

    original_observations, original_relations = _maps(original)
    candidate_observations, candidate_relations = _maps(candidate)
    obs_added, obs_removed, obs_modified = _diff_ids(
        original_observations, candidate_observations
    )
    rel_added, rel_removed, rel_modified = _diff_ids(
        original_relations, candidate_relations
    )

    findings = {finding.id: finding for finding in audit.findings}
    covered_added: set[tuple[SurveyCorrectionObjectType, str]] = set()
    covered_removed: set[tuple[SurveyCorrectionObjectType, str]] = set()
    covered_modified: set[tuple[SurveyCorrectionObjectType, str]] = set()

    for change in correction.changes:
        finding = findings.get(change.finding_id)
        if finding is None:
            issues.append(
                SurveyCorrectionValidationIssue(
                    code="survey_correction_unknown_finding",
                    change_id=change.id,
                    message=f"Unknown SurveyAudit finding {change.finding_id!r}.",
                )
            )
            continue
        if finding.severity not in {
            SurveyAuditSeverity.WARNING,
            SurveyAuditSeverity.ERROR,
        } or finding.suggested_action is SurveyAuditSuggestedAction.KEEP:
            issues.append(
                SurveyCorrectionValidationIssue(
                    code="survey_correction_non_actionable_finding",
                    change_id=change.id,
                    message="Correction changes must be tied to actionable warning/error findings.",
                )
            )
        if change.action is not finding.suggested_action:
            issues.append(
                SurveyCorrectionValidationIssue(
                    code="survey_correction_action_mismatch",
                    change_id=change.id,
                    message=(
                        f"Change action {change.action.value!r} does not match finding "
                        f"action {finding.suggested_action.value!r}."
                    ),
                )
            )

        if finding.target_type is SurveyAuditTargetType.OBSERVATION:
            if change.object_type is not SurveyCorrectionObjectType.OBSERVATION:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_target_type_mismatch",
                        change_id=change.id,
                        message="Observation finding must correct an observation.",
                    )
                )
            if finding.target_id and change.source_id != finding.target_id:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_source_target_mismatch",
                        change_id=change.id,
                        message="Correction source_id must match the audited observation target.",
                    )
                )
        elif finding.target_type is SurveyAuditTargetType.RELATION:
            if change.object_type is not SurveyCorrectionObjectType.RELATION:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_target_type_mismatch",
                        change_id=change.id,
                        message="Relation finding must correct a relation.",
                    )
                )
            if finding.target_id and change.source_id != finding.target_id:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_source_target_mismatch",
                        change_id=change.id,
                        message="Correction source_id must match the audited relation target.",
                    )
                )
        elif finding.target_type is not SurveyAuditTargetType.SURVEY:
            issues.append(
                SurveyCorrectionValidationIssue(
                    code="survey_correction_unsupported_finding_target",
                    change_id=change.id,
                    message="Photo-level findings cannot directly mutate Survey objects in v0.1.",
                )
            )

        if change.object_type is SurveyCorrectionObjectType.OBSERVATION:
            added, removed, modified = obs_added, obs_removed, obs_modified
            before, after = original_observations, candidate_observations
        else:
            added, removed, modified = rel_added, rel_removed, rel_modified
            before, after = original_relations, candidate_relations

        if change.action is SurveyAuditSuggestedAction.ADD:
            assert change.candidate_id is not None
            if change.candidate_id not in added:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_add_not_new",
                        change_id=change.id,
                        message="add must point to an object newly present in the candidate.",
                    )
                )
            covered_added.add((change.object_type, change.candidate_id))
        elif change.action is SurveyAuditSuggestedAction.REMOVE:
            assert change.source_id is not None
            if change.source_id not in removed:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_remove_not_removed",
                        change_id=change.id,
                        message="remove must point to an object absent from the candidate.",
                    )
                )
            covered_removed.add((change.object_type, change.source_id))
        elif change.action in {
            SurveyAuditSuggestedAction.LOWER_CERTAINTY,
            SurveyAuditSuggestedAction.REORIENT,
        }:
            assert change.source_id is not None
            if change.source_id not in modified:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_in_place_not_modified",
                        change_id=change.id,
                        message="in-place correction must actually modify the targeted object.",
                    )
                )
            elif change.source_id in before and change.source_id in after:
                if change.action is SurveyAuditSuggestedAction.LOWER_CERTAINTY:
                    issues.extend(
                        _validate_lower_certainty_scope(
                            change,
                            before[change.source_id],
                            after[change.source_id],
                        )
                    )
                else:
                    issues.extend(
                        _validate_reorient_scope(
                            change,
                            before[change.source_id],
                            after[change.source_id],
                        )
                    )
            covered_modified.add((change.object_type, change.source_id))
        elif change.action is SurveyAuditSuggestedAction.MERGE:
            assert change.source_id is not None and change.candidate_id is not None
            if change.source_id not in removed:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_merge_source_not_removed",
                        change_id=change.id,
                        message="merge source must be removed from the candidate.",
                    )
                )
            if change.candidate_id not in after:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_merge_target_missing",
                        change_id=change.id,
                        message="merge target must exist in the candidate.",
                    )
                )
            if change.source_id not in before:
                issues.append(
                    SurveyCorrectionValidationIssue(
                        code="survey_correction_merge_source_missing",
                        change_id=change.id,
                        message="merge source must exist in the original Survey.",
                    )
                )
            issues.append(
                SurveyCorrectionValidationIssue(
                    code="survey_correction_merge_requires_manual_review",
                    change_id=change.id,
                    message=(
                        "SurveyCorrection v0.1 does not automatically validate merge semantics; "
                        "duplicate-object merges require explicit manual review."
                    ),
                )
            )
            covered_removed.add((change.object_type, change.source_id))
            if change.candidate_id in modified:
                covered_modified.add((change.object_type, change.candidate_id))

    expected_added = {
        *((SurveyCorrectionObjectType.OBSERVATION, item_id) for item_id in obs_added),
        *((SurveyCorrectionObjectType.RELATION, item_id) for item_id in rel_added),
    }
    expected_removed = {
        *((SurveyCorrectionObjectType.OBSERVATION, item_id) for item_id in obs_removed),
        *((SurveyCorrectionObjectType.RELATION, item_id) for item_id in rel_removed),
    }
    expected_modified = {
        *((SurveyCorrectionObjectType.OBSERVATION, item_id) for item_id in obs_modified),
        *((SurveyCorrectionObjectType.RELATION, item_id) for item_id in rel_modified),
    }

    for kind, item_id in sorted(expected_added - covered_added, key=lambda item: (item[0].value, item[1])):
        issues.append(
            SurveyCorrectionValidationIssue(
                code="survey_correction_undeclared_addition",
                change_id=None,
                message=f"Added {kind.value} {item_id!r} is not tied to a correction change.",
            )
        )
    for kind, item_id in sorted(expected_removed - covered_removed, key=lambda item: (item[0].value, item[1])):
        issues.append(
            SurveyCorrectionValidationIssue(
                code="survey_correction_undeclared_removal",
                change_id=None,
                message=f"Removed {kind.value} {item_id!r} is not tied to a correction change.",
            )
        )
    for kind, item_id in sorted(expected_modified - covered_modified, key=lambda item: (item[0].value, item[1])):
        issues.append(
            SurveyCorrectionValidationIssue(
                code="survey_correction_undeclared_modification",
                change_id=None,
                message=f"Modified {kind.value} {item_id!r} is not tied to a correction change.",
            )
        )

    semantic_issues = [
        *validate_survey_semantics(candidate),
        *validate_multiview_roof_hypotheses(candidate),
    ]
    for issue in semantic_issues:
        issues.append(
            SurveyCorrectionValidationIssue(
                code=f"survey_correction_candidate_{issue.code}",
                change_id=None,
                message=issue.message,
                severity=issue.severity,
            )
        )

    return issues
