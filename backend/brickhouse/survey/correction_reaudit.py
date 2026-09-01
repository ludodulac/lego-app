"""Deterministic scope builder for a targeted post-correction visual re-audit.

The scope is intentionally narrow: changed observations/relations, relations
incident to changed observations, and the source photos already referenced by
those objects. It never mutates either Survey and never launches an AI loop.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .correction import SurveyCorrection, SurveyCorrectionObjectType
from .models import ArchitecturalSurvey, SurveyObservation, SurveyRelation


class SurveyCorrectionReauditScope(BaseModel):
    correction_change_ids: list[str] = Field(default_factory=list)
    observation_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    photo_indexes: list[int] = Field(default_factory=list)


def _objects_by_id(survey: ArchitecturalSurvey):
    return (
        {item.id: item for item in survey.observations},
        {item.id: item for item in survey.relations},
    )


def _evidence_photo_indexes(
    objects: list[SurveyObservation | SurveyRelation],
) -> set[int]:
    return {
        evidence.photo_index
        for item in objects
        for evidence in item.evidence
    }


def build_survey_correction_reaudit_scope(
    original: ArchitecturalSurvey,
    correction: SurveyCorrection,
) -> SurveyCorrectionReauditScope:
    """Build the minimum deterministic neighborhood to inspect after correction.

    For an observation change, directly incident relations are included so a
    local correction cannot silently break topology. Removed objects are read
    from the original Survey; added/modified objects are read from the candidate.
    """
    candidate = correction.candidate
    original_observations, original_relations = _objects_by_id(original)
    candidate_observations, candidate_relations = _objects_by_id(candidate)

    observation_ids: set[str] = set()
    relation_ids: set[str] = set()

    for change in correction.changes:
        ids = {item_id for item_id in (change.source_id, change.candidate_id) if item_id}
        if change.object_type is SurveyCorrectionObjectType.OBSERVATION:
            observation_ids.update(ids)
        else:
            relation_ids.update(ids)

    # Include topology directly touching a changed observation on either side of
    # the correction. This catches removal/addition/reorientation regressions
    # without broadening the scope to an unconstrained full independent audit.
    for relation in [*original.relations, *candidate.relations]:
        if (
            relation.subject_id in observation_ids
            or relation.object_id in observation_ids
        ):
            relation_ids.add(relation.id)

    scoped_objects: list[SurveyObservation | SurveyRelation] = []
    for item_id in observation_ids:
        if item_id in original_observations:
            scoped_objects.append(original_observations[item_id])
        if item_id in candidate_observations:
            scoped_objects.append(candidate_observations[item_id])
    for item_id in relation_ids:
        if item_id in original_relations:
            scoped_objects.append(original_relations[item_id])
        if item_id in candidate_relations:
            scoped_objects.append(candidate_relations[item_id])

    return SurveyCorrectionReauditScope(
        correction_change_ids=[change.id for change in correction.changes],
        observation_ids=sorted(observation_ids),
        relation_ids=sorted(relation_ids),
        photo_indexes=sorted(_evidence_photo_indexes(scoped_objects)),
    )
