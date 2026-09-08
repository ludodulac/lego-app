"""Deterministic scope builder for a targeted post-correction visual re-audit.

The scope is intentionally narrow: changed photos/observations/relations,
orientation-bearing observations whose evidence depends directly on a changed
photo, relations incident to changed/dependent observations, and source photos
already referenced by those objects. It never mutates either Survey and never
launches an AI loop.
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


def _references_any_photo(
    item: SurveyObservation | SurveyRelation,
    photo_indexes: set[int],
) -> bool:
    return any(evidence.photo_index in photo_indexes for evidence in item.evidence)


def _observation_has_orientation_claim(observation: SurveyObservation) -> bool:
    return observation.facade is not None or any(
        key in observation.attributes
        for key in ("facade_horizontal_rank", "facade_vertical_rank")
    )


def build_survey_correction_reaudit_scope(
    original: ArchitecturalSurvey,
    correction: SurveyCorrection,
) -> SurveyCorrectionReauditScope:
    """Build the minimum deterministic neighborhood to inspect after correction.

    Observation changes include directly incident relations so a local correction
    cannot silently break topology. A photo reorientation includes observations
    that both cite the photo and carry facade/rank orientation, plus relations
    that cite the photo directly. Relations incident to those observations are
    included as the local topology boundary. Global observations that merely cite
    many photos do not explode one photo correction into a near-full Survey audit.
    Removed objects are read from the original Survey; added/modified objects are
    read from the candidate.
    """
    candidate = correction.candidate
    original_observations, original_relations = _objects_by_id(original)
    candidate_observations, candidate_relations = _objects_by_id(candidate)

    observation_ids: set[str] = set()
    relation_ids: set[str] = set()
    direct_photo_indexes: set[int] = set()

    for change in correction.changes:
        ids = {item_id for item_id in (change.source_id, change.candidate_id) if item_id}
        if change.object_type is SurveyCorrectionObjectType.PHOTO:
            for item_id in ids:
                try:
                    photo_index = int(item_id)
                except ValueError:
                    continue
                if photo_index >= 1:
                    direct_photo_indexes.add(photo_index)
        elif change.object_type is SurveyCorrectionObjectType.OBSERVATION:
            observation_ids.update(ids)
        else:
            relation_ids.update(ids)

    if direct_photo_indexes:
        for observation in [*original.observations, *candidate.observations]:
            if (
                _observation_has_orientation_claim(observation)
                and _references_any_photo(observation, direct_photo_indexes)
            ):
                observation_ids.add(observation.id)
        for relation in [*original.relations, *candidate.relations]:
            if _references_any_photo(relation, direct_photo_indexes):
                relation_ids.add(relation.id)

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
        photo_indexes=sorted(
            direct_photo_indexes | _evidence_photo_indexes(scoped_objects)
        ),
    )
