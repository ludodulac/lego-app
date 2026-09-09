"""Non-metric user-confirmed spatial relations between accepted Survey observations.

These facts are a provenance sidecar. They deliberately do not mutate the accepted
ArchitecturalSurvey or create measurements. The first vocabulary is qualitative
vertical ordering, which can constrain Scene geometry without pretending a height
difference was measured.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind

from .models import ArchitecturalSurvey, Certainty


HumanLevelRelation = Literal["lower_than", "higher_than", "same_level"]


class HumanRelativeLevelFact(BaseModel):
    subject_observation_id: str = Field(min_length=1)
    object_observation_id: str = Field(min_length=1)
    relation: HumanLevelRelation
    certainty: Certainty = Certainty.CERTAIN
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_fact(self) -> "HumanRelativeLevelFact":
        if self.subject_observation_id == self.object_observation_id:
            raise ValueError("human relative-level fact subject and object must differ")
        if self.source.kind is not SourceKind.USER_PROVIDED:
            raise ValueError("human relative-level facts require source.kind=user_provided")
        return self


class HumanRelativeLevelFactSet(BaseModel):
    source_survey_id: str
    facts: list[HumanRelativeLevelFact] = Field(min_length=1)


def _canonical_ordering(fact: HumanRelativeLevelFact) -> tuple[str, str] | None:
    if fact.relation == "lower_than":
        return fact.subject_observation_id, fact.object_observation_id
    if fact.relation == "higher_than":
        return fact.object_observation_id, fact.subject_observation_id
    return None


def validate_human_relative_level_facts(
    survey: ArchitecturalSurvey,
    facts: list[HumanRelativeLevelFact],
) -> HumanRelativeLevelFactSet:
    """Validate user spatial facts against Survey identity without editing Survey."""
    if not facts:
        raise ValueError("at least one human relative-level fact is required")

    observation_ids = {item.id for item in survey.observations}
    ordering_pairs: set[tuple[str, str]] = set()
    same_pairs: set[tuple[str, str]] = set()

    for fact in facts:
        for observation_id in (fact.subject_observation_id, fact.object_observation_id):
            if observation_id not in observation_ids:
                raise ValueError(f"human relative-level fact references unknown observation {observation_id!r}")

        ordered = _canonical_ordering(fact)
        unordered = tuple(sorted((fact.subject_observation_id, fact.object_observation_id)))
        if ordered is None:
            if unordered in same_pairs:
                raise ValueError("duplicate human same-level fact")
            if ordered_reverse_conflict(unordered, ordering_pairs):
                raise ValueError("human relative-level facts contradict same_level")
            same_pairs.add(unordered)
            continue

        if ordered in ordering_pairs:
            raise ValueError("duplicate human relative-level ordering fact")
        if (ordered[1], ordered[0]) in ordering_pairs:
            raise ValueError("human relative-level facts contain contradictory inverse ordering")
        if unordered in same_pairs:
            raise ValueError("human relative-level facts contradict same_level")
        ordering_pairs.add(ordered)

    return HumanRelativeLevelFactSet(source_survey_id=survey.id, facts=facts)


def ordered_reverse_conflict(
    unordered: tuple[str, str],
    ordering_pairs: set[tuple[str, str]],
) -> bool:
    a, b = unordered
    return (a, b) in ordering_pairs or (b, a) in ordering_pairs
