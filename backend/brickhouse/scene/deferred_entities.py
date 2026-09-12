"""Append-only Scene support for certain Survey entities without resolved geometry.

A deferred entity is only a reference back to an accepted Survey observation. It
preserves existence/identity without duplicating semantic attributes or inventing
Scene geometry. Metric projection remains blocked until every deferred entity is
promoted to a fully resolved Scene primitive.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .multi_run_stair_fidelity import validate_scene_against_survey as _validate_existing
from .projection import ProjectionIssue, ProjectionResult, ProjectionSeverity
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology_projection import project_scene_to_building as _project_existing
from .wall_profile_scene import ArchitecturalScene as _ArchitecturalScene


class DeferredEntityKind(str, Enum):
    OPENING = "opening"
    CHIMNEY = "chimney"


class DeferredCertainEntity(BaseModel):
    """Reference a certain Survey entity whose Scene geometry is unresolved."""

    survey_id: str = Field(min_length=1)
    kind: DeferredEntityKind
    geometry_status: Literal["unresolved"] = "unresolved"
    reason: str | None = None


class ArchitecturalScene(_ArchitecturalScene):
    """ArchitecturalScene with explicit non-promoted certain Survey entities."""

    deferred_entities: list[DeferredCertainEntity] = Field(default_factory=list)

    def _validate_ids_and_references(self):
        super()._validate_ids_and_references()
        deferred_ids = [item.survey_id for item in self.deferred_entities]
        if len(deferred_ids) != len(set(deferred_ids)):
            raise ValueError("deferred entity survey IDs must be unique")
        promoted_ids = {
            item.id
            for item in [
                *self.volumes,
                *self.openings,
                *self.roofs,
                *self.chimneys,
                *self.platforms,
                *self.stairs,
                *self.equipment,
            ]
        }
        collision = promoted_ids.intersection(deferred_ids)
        if collision:
            raise ValueError(
                "a Survey entity cannot be both deferred and promoted in Scene: "
                + ", ".join(sorted(collision))
            )


def _survey_kind(kind: DeferredEntityKind) -> ObservationKind:
    if kind is DeferredEntityKind.OPENING:
        return ObservationKind.OPENING
    return ObservationKind.CHIMNEY


def _semantic_type_explicitly_uncertain(observation) -> bool:
    """Only explicit plausible/unproven certainty relaxes the legacy type gate.

    Older accepted Surveys may have no per-attribute certainty metadata at all;
    those retain the historical strict semantic_type behavior.
    """

    certainty = observation.attribute_certainty.get("semantic_type")
    return certainty in {
        Certainty.PLAUSIBLE,
        Certainty.UNPROVEN,
        Certainty.PLAUSIBLE.value,
        Certainty.UNPROVEN.value,
    }


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Preserve fidelity while accepting explicit, geometry-unresolved references."""

    existing = list(_validate_existing(survey, scene))
    survey_by_id = {item.id: item for item in survey.observations}
    deferred = {item.survey_id: item for item in scene.deferred_entities}

    issues: list[SceneSurveyIssue] = []
    for item in scene.deferred_entities:
        observation = survey_by_id.get(item.survey_id)
        if observation is None:
            issues.append(SceneSurveyIssue(
                code="deferred_entity_not_in_survey",
                severity=SceneSurveySeverity.ERROR,
                object_id=item.survey_id,
                message=f"L’entité différée {item.survey_id!r} n’existe pas dans le Survey accepté.",
            ))
            continue
        if observation.certainty is not Certainty.CERTAIN:
            issues.append(SceneSurveyIssue(
                code="deferred_entity_not_certain",
                severity=SceneSurveySeverity.ERROR,
                object_id=item.survey_id,
                message=f"L’entité différée {item.survey_id!r} n’est pas certaine dans le Survey.",
            ))
        if observation.kind is not _survey_kind(item.kind):
            issues.append(SceneSurveyIssue(
                code="deferred_entity_kind_drift",
                severity=SceneSurveySeverity.ERROR,
                object_id=item.survey_id,
                message=f"Le kind différé de {item.survey_id!r} ne correspond pas au Survey.",
            ))

    certain_chimneys = {
        item.id
        for item in survey.observations
        if item.kind is ObservationKind.CHIMNEY and item.certainty is Certainty.CERTAIN
    }
    promoted_chimneys = {item.id for item in scene.chimneys}
    deferred_chimneys = {
        item.survey_id
        for item in scene.deferred_entities
        if item.kind is DeferredEntityKind.CHIMNEY
    }
    missing_chimneys = certain_chimneys - promoted_chimneys
    all_missing_chimneys_deferred = bool(missing_chimneys) and missing_chimneys <= deferred_chimneys

    for issue in existing:
        observation = survey_by_id.get(issue.object_id) if issue.object_id else None
        if (
            issue.code == "opening_type_drift"
            and observation is not None
            and _semantic_type_explicitly_uncertain(observation)
        ):
            # Object existence may be certain while semantic_type is only plausible
            # or unproven. Scene type=unknown is then the conservative result.
            continue
        if (
            issue.code == "certain_opening_missing"
            and issue.object_id in deferred
            and deferred[issue.object_id].kind is DeferredEntityKind.OPENING
        ):
            continue
        if issue.code == "certain_chimney_missing" and all_missing_chimneys_deferred:
            continue
        issues.append(issue)

    return issues


def project_scene_to_building(scene: ArchitecturalScene) -> ProjectionResult:
    """Block metric/LEGO projection while any certain entity remains deferred."""

    result = _project_existing(scene)
    if not scene.deferred_entities:
        return result

    issues = [*result.issues]
    for item in scene.deferred_entities:
        issues.append(ProjectionIssue(
            code="certain_entity_geometry_unresolved",
            severity=ProjectionSeverity.BLOCKER,
            object_id=item.survey_id,
            message=(
                f"L’entité certaine {item.survey_id!r} est conservée depuis le Survey mais n’a pas encore "
                "de géométrie Scene résolue. La projection BuildingModel/LEGO reste bloquée plutôt que "
                "d’inventer sa façade, son ownership ou ses métriques."
            ),
        ))
    return result.model_copy(update={"building": None, "issues": issues})
