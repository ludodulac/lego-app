"""Semantic validation helpers for ArchitecturalSurvey."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ArchitecturalSurvey, Certainty, ObservationKind


@dataclass(frozen=True)
class SurveyValidationIssue:
    code: str
    observation_id: str | None
    message: str
    severity: str = "error"


def validate_survey_semantics(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Return semantic issues that Pydantic shape validation alone cannot catch."""
    issues: list[SurveyValidationIssue] = []

    for observation in survey.observations:
        attributes = observation.attributes

        if observation.kind is ObservationKind.OPENING:
            confirmed = bool(attributes.get("confirmed_by_user", False))
            semantic_role = attributes.get("semantic_role") or attributes.get("semantic_type")
            if confirmed and (not isinstance(semantic_role, str) or not semantic_role.strip()):
                issues.append(SurveyValidationIssue(
                    code="confirmed_opening_missing_semantic_role",
                    observation_id=observation.id,
                    message="User-confirmed opening requires a stable semantic_role; visual ambiguity may not erase its identity.",
                ))

            target_ownership = attributes.get("target_building_ownership")
            if observation.certainty in {Certainty.CERTAIN, Certainty.PLAUSIBLE}:
                if target_ownership == "unproven":
                    issues.append(SurveyValidationIssue(
                        code="opening_target_ownership_unproven",
                        observation_id=observation.id,
                        message="Opening ownership by the target building is unproven; mark the observation unproven or context until new evidence exists.",
                    ))

        if observation.kind is ObservationKind.ROOF:
            roof_edge = attributes.get("roof_edge_type")
            if observation.facade is not None and observation.facade.value == "front":
                gable_end = attributes.get("facade_roof_relationship") == "gable_end"
                if gable_end and roof_edge == "eave_across_facade":
                    issues.append(SurveyValidationIssue(
                        code="gable_eave_terminology_conflict",
                        observation_id=observation.id,
                        message="A gable-end front facade cannot simultaneously have a horizontal eave across that facade; use rake/gable-edge terminology.",
                    ))

    return issues
