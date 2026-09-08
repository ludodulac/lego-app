"""API-facing adapter for provenance-preserving human-fact Scene handoffs.

This module deliberately contains no HTTP framework wiring.  It gives the active
API boundary a small typed adapter that can be mounted without duplicating the
Survey overlay rules in FastAPI or in the browser.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .human_facts import HumanAttributeFact
from .models import ArchitecturalSurvey
from .scene_handoff import HumanFactSceneHandoff, build_scene_handoff_with_human_facts


class HumanFactSceneHandoffRequest(BaseModel):
    """Accepted source Survey plus explicit user-confirmed semantic facts."""

    survey: ArchitecturalSurvey
    human_facts: list[HumanAttributeFact] = Field(min_length=1)


def prepare_human_fact_scene_handoff(
    request: HumanFactSceneHandoffRequest,
) -> HumanFactSceneHandoff:
    """Validate facts once and return the exact derived Scene-input artifact.

    The browser/API layer must serialize this result rather than applying facts
    itself.  This keeps accepted Survey truth, provenance and conflict handling
    on the backend contract already covered by ``scene_handoff``.
    """
    return build_scene_handoff_with_human_facts(request.survey, request.human_facts)
