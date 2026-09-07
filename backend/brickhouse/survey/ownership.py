"""Target-vs-context ownership semantics for photo-derived Survey observations.

Ownership is intentionally non-metric and additive. Legacy Surveys that do not
carry ``attributes.subject_ownership`` remain valid. When ownership is present,
it becomes an explicit semantic claim whose certainty is stored through the
existing per-attribute certainty map.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from .models import ArchitecturalSurvey, Certainty, ObservationKind, RelationKind
from .validation import SurveyValidationIssue


class SubjectOwnership(str, Enum):
    TARGET_BUILDING = "target_building"
    EXTERNAL_CONTEXT = "external_context"
    UNRESOLVED = "unresolved"


class OwnershipFacts(BaseModel):
    observation_id: str
    ownership: SubjectOwnership
    certainty: Certainty
    evidence_photo_indexes: list[int]


class OwnershipReport(BaseModel):
    facts: list[OwnershipFacts]
    issues: list[SurveyValidationIssue]

    model_config = {"arbitrary_types_allowed": True}


def _issue(observation_id: str | None, code: str, message: str) -> SurveyValidationIssue:
    return SurveyValidationIssue(code=code, observation_id=observation_id, message=message)


def analyze_subject_ownership(survey: ArchitecturalSurvey) -> OwnershipReport:
    """Read explicit ownership claims without inferring them from facade position.

    A facade label, image-side position, geometric adjacency or visual overlap is
    never enough by itself to classify an object as part of the target building.
    This function only validates ownership already encoded in the Survey.
    """

    facts: list[OwnershipFacts] = []
    issues: list[SurveyValidationIssue] = []

    for observation in sorted(survey.observations, key=lambda item: item.id):
        raw = observation.attributes.get("subject_ownership")
        if raw is None:
            continue
        try:
            ownership = SubjectOwnership(raw)
        except (TypeError, ValueError):
            issues.append(_issue(
                observation.id,
                "invalid_subject_ownership",
                "attributes.subject_ownership must be target_building, external_context, or unresolved",
            ))
            continue

        certainty = observation.certainty_for_attribute("subject_ownership")
        if ownership is SubjectOwnership.UNRESOLVED and certainty is Certainty.CERTAIN:
            issues.append(_issue(
                observation.id,
                "unresolved_ownership_cannot_be_certain",
                "subject_ownership='unresolved' cannot carry certainty='certain'",
            ))
        if observation.kind is ObservationKind.CONTEXT and ownership is SubjectOwnership.TARGET_BUILDING:
            issues.append(_issue(
                observation.id,
                "context_observation_cannot_be_target_owned",
                "a kind='context' observation cannot simultaneously claim target_building ownership",
            ))

        facts.append(OwnershipFacts(
            observation_id=observation.id,
            ownership=ownership,
            certainty=certainty,
            evidence_photo_indexes=sorted({item.photo_index for item in observation.evidence}),
        ))

    ownership_by_id = {item.observation_id: item for item in facts}
    identity_relations = {RelationKind.PART_OF, RelationKind.SAME_PHYSICAL_OBJECT}
    for relation in survey.relations:
        if relation.kind not in identity_relations or relation.certainty is not Certainty.CERTAIN:
            continue
        subject = ownership_by_id.get(relation.subject_id)
        object_ = ownership_by_id.get(relation.object_id)
        if subject is None or object_ is None:
            continue
        if subject.certainty is not Certainty.CERTAIN or object_.certainty is not Certainty.CERTAIN:
            continue
        certain_roles = {subject.ownership, object_.ownership}
        if SubjectOwnership.TARGET_BUILDING in certain_roles and SubjectOwnership.EXTERNAL_CONTEXT in certain_roles:
            issues.append(_issue(
                relation.subject_id,
                "contradictory_ownership_identity_relation",
                (
                    f"certain relation {relation.id!r} ({relation.kind.value}) links target-owned and "
                    "external-context observations; ownership must be resolved before reconstruction"
                ),
            ))

    return OwnershipReport(facts=facts, issues=issues)


def validate_subject_ownership(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Return ownership contract issues for normal Survey semantic validation."""

    return analyze_subject_ownership(survey).issues
