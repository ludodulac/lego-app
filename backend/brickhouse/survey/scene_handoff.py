"""Build a provenance-preserving Survey -> Scene handoff candidate.

The accepted ArchitecturalSurvey remains immutable source truth. Explicit
user-confirmed semantic facts are applied through ``apply_human_attribute_facts``
and carried alongside the derived candidate so downstream Scene reasoning can
use them without losing provenance or rewriting the accepted Survey.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .human_facts import HumanAttributeFact, apply_human_attribute_facts
from .models import ArchitecturalSurvey


class HumanFactSceneHandoff(BaseModel):
    """Derived Survey input plus exact user-fact provenance for Scene reasoning."""

    source_survey_id: str
    scene_input_survey: ArchitecturalSurvey
    human_facts: list[HumanAttributeFact] = Field(min_length=1)


def build_scene_handoff_with_human_facts(
    survey: ArchitecturalSurvey,
    facts: list[HumanAttributeFact],
) -> HumanFactSceneHandoff:
    """Apply explicit user facts and return the validated downstream handoff.

    This function performs no metric inference. In particular it never creates,
    removes or rewrites ``known_measurements``; semantic human facts may enrich
    observation attributes while measurement authority remains exactly where it
    was in the accepted Survey.
    """
    application = apply_human_attribute_facts(survey, facts)

    if application.candidate.known_measurements != survey.known_measurements:
        raise ValueError("human semantic facts must not rewrite known_measurements")

    return HumanFactSceneHandoff(
        source_survey_id=application.source_survey_id,
        scene_input_survey=application.candidate,
        human_facts=application.facts,
    )
