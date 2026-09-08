"""Explicit user-confirmed semantic facts applied as a non-destructive Survey overlay.

The accepted ArchitecturalSurvey remains source truth.  A HumanAttributeFact is a
separate provenance-bearing instruction that can enrich a downstream candidate
without rewriting the accepted source document.  This is intended for facts that
a user can clarify after photo analysis (opening type, stair topology, material,
etc.) while exact metric geometry remains unknown.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind

from .models import ArchitecturalSurvey, Certainty
from .validation import validate_survey_semantics


class HumanAttributeFact(BaseModel):
    observation_id: str = Field(min_length=1)
    attribute_name: str = Field(min_length=1)
    value: Any
    certainty: Certainty = Certainty.CERTAIN
    source: SourceInfo
    statement: str = Field(min_length=1)
    supersedes_existing: bool = False

    @model_validator(mode="after")
    def validate_user_source(self) -> "HumanAttributeFact":
        if self.source.kind is not SourceKind.USER_PROVIDED:
            raise ValueError("human attribute facts require source.kind=user_provided")
        return self


class HumanFactApplication(BaseModel):
    source_survey_id: str
    candidate: ArchitecturalSurvey
    facts: list[HumanAttributeFact] = Field(min_length=1)


def apply_human_attribute_facts(
    survey: ArchitecturalSurvey,
    facts: list[HumanAttributeFact],
) -> HumanFactApplication:
    """Return a validated downstream candidate while leaving ``survey`` untouched.

    No interpretation is performed here: the exact supplied attribute value is
    copied onto the target observation.  Existing contradictory content may only
    be replaced when the fact explicitly declares ``supersedes_existing``.
    """
    if not facts:
        raise ValueError("at least one human attribute fact is required")

    keys = [(fact.observation_id, fact.attribute_name) for fact in facts]
    if len(keys) != len(set(keys)):
        raise ValueError("human attribute facts must target unique observation attributes")

    candidate = survey.model_copy(deep=True)
    observations = {item.id: item for item in candidate.observations}

    for fact in facts:
        observation = observations.get(fact.observation_id)
        if observation is None:
            raise ValueError(f"human fact references unknown observation {fact.observation_id!r}")

        existing = observation.attributes.get(fact.attribute_name)
        if (
            fact.attribute_name in observation.attributes
            and existing != fact.value
            and not fact.supersedes_existing
        ):
            raise ValueError(
                f"human fact for {fact.observation_id!r}.{fact.attribute_name} conflicts with existing value; "
                "set supersedes_existing=true only for an explicit user correction"
            )

        observation.attributes[fact.attribute_name] = fact.value
        observation.attribute_certainty[fact.attribute_name] = fact.certainty

    semantic_issues = validate_survey_semantics(candidate)
    if semantic_issues:
        first = semantic_issues[0]
        raise ValueError(
            f"human fact candidate violates Survey semantics: {first.code}: {first.message}"
        )

    return HumanFactApplication(
        source_survey_id=survey.id,
        candidate=candidate,
        facts=facts,
    )
