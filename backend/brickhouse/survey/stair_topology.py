"""Non-metric stair-system topology preserved before Scene metrification.

ArchitecturalSurvey remains the semantic authority.  This module interprets only
explicit stair topology attributes; it never invents run coordinates, lengths,
angles, tread counts, or landing dimensions.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from .models import ArchitecturalSurvey, Certainty, ObservationKind
from .validation import SurveyValidationIssue


TurningNodeKind = Literal["turn", "landing", "turn_or_landing"]


class StairTopologyValue(BaseModel):
    """Evidence-backed topology for one architectural stair system.

    ``minimum_run_count`` is intentionally different from ``exact_run_count``:
    seeing a direction change can prove that at least two runs exist without
    proving how many runs are hidden or their metric geometry.
    """

    minimum_run_count: int | None = Field(default=None, ge=1)
    exact_run_count: int | None = Field(default=None, ge=1)
    direction_change: bool | None = None
    turning_node_kind: TurningNodeKind | None = None
    component_run_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> "StairTopologyValue":
        if (
            self.minimum_run_count is not None
            and self.exact_run_count is not None
            and self.exact_run_count < self.minimum_run_count
        ):
            raise ValueError("exact_run_count cannot be smaller than minimum_run_count")
        if self.exact_run_count == 1 and self.direction_change is True:
            raise ValueError("a single exact run cannot also contain a direction change")
        if self.exact_run_count == 1 and self.turning_node_kind is not None:
            raise ValueError("a single exact run cannot also define a turning node")
        if self.turning_node_kind == "turn" and self.direction_change is False:
            raise ValueError("an explicit turn cannot coexist with direction_change=false")
        if len(self.component_run_ids) != len(set(self.component_run_ids)):
            raise ValueError("component_run_ids must be unique")
        return self


class StairTopologyFacts(BaseModel):
    """Typed, non-metric facts available to Survey -> Scene reasoning."""

    observation_id: str
    topology: StairTopologyValue
    certainty: Certainty
    requires_multiple_scene_runs: bool


class StairTopologyReport(BaseModel):
    facts: list[StairTopologyFacts] = Field(default_factory=list)
    issues: list[SurveyValidationIssue] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


def _issue(observation_id: str, code: str, message: str) -> SurveyValidationIssue:
    return SurveyValidationIssue(code=code, observation_id=observation_id, message=message)


def analyze_survey_stair_topology(survey: ArchitecturalSurvey) -> StairTopologyReport:
    """Read explicit ``attributes.stair_topology`` without metric inference.

    Component IDs, when supplied, must reference other stair observations.  The
    function is deterministic and does not mutate the Survey.
    """

    observations = {item.id: item for item in survey.observations}
    facts: list[StairTopologyFacts] = []
    issues: list[SurveyValidationIssue] = []

    for observation in sorted(survey.observations, key=lambda item: item.id):
        if observation.kind is not ObservationKind.STAIR:
            continue
        raw = observation.attributes.get("stair_topology")
        if raw is None:
            continue
        try:
            topology = StairTopologyValue.model_validate(raw)
        except ValidationError as exc:
            issues.append(_issue(
                observation.id,
                "invalid_stair_topology",
                f"attributes.stair_topology is inconsistent: {exc.errors()[0]['msg']}",
            ))
            continue

        for component_id in topology.component_run_ids:
            component = observations.get(component_id)
            if component is None:
                issues.append(_issue(
                    observation.id,
                    "stair_component_missing",
                    f"stair topology references missing component run {component_id!r}",
                ))
            elif component.kind is not ObservationKind.STAIR:
                issues.append(_issue(
                    observation.id,
                    "stair_component_not_stair",
                    f"stair topology component {component_id!r} is not a stair observation",
                ))
            elif component_id == observation.id:
                issues.append(_issue(
                    observation.id,
                    "stair_component_self_reference",
                    "a stair system cannot list itself as a component run",
                ))

        proven_minimum = topology.minimum_run_count or 1
        if topology.exact_run_count is not None:
            proven_minimum = max(proven_minimum, topology.exact_run_count)
        if topology.direction_change is True or topology.turning_node_kind is not None:
            proven_minimum = max(proven_minimum, 2)
        if topology.component_run_ids:
            proven_minimum = max(proven_minimum, len(topology.component_run_ids))

        certainty = observation.certainty_for_attribute("stair_topology")
        facts.append(StairTopologyFacts(
            observation_id=observation.id,
            topology=topology,
            certainty=certainty,
            requires_multiple_scene_runs=proven_minimum >= 2,
        ))

    return StairTopologyReport(facts=facts, issues=issues)


def validate_stair_topology_observations(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Return only topology contract problems for the normal Survey validator."""

    return analyze_survey_stair_topology(survey).issues
