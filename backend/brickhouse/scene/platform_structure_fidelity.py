"""Preserve evidence-backed terrace/deck structure across Survey -> Scene.

This layer is deliberately additive.  Metric support geometry belongs in
``Platform.supports`` when the photos constrain it; visibly present structure whose
count/coordinates are not yet resolved belongs in
``platform_structure_observations``.  Losing the structure entirely is different
from honestly keeping its metric details unresolved.
"""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import EdgeTreatment
from .platform_structure import PlatformStructureKind
from .roof_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import ArchitecturalScene


_SUPPORT_KINDS = {
    PlatformStructureKind.VERTICAL_POST,
    PlatformStructureKind.DIAGONAL_BRACE,
}


def _has_preserved_support_structure(scene: ArchitecturalScene, platform_id: str) -> bool:
    platform = next((item for item in scene.platforms if item.id == platform_id), None)
    if platform is None:
        return False
    if platform.supports:
        return True
    return any(
        item.platform_id == platform_id and item.kind in _SUPPORT_KINDS
        for item in scene.platform_structure_observations
    )


def _has_preserved_guardrail(scene: ArchitecturalScene, platform_id: str) -> bool:
    platform = next((item for item in scene.platforms if item.id == platform_id), None)
    if platform is None:
        return False
    if platform.edge_treatment is EdgeTreatment.OPEN_RAILING:
        return True
    if platform.edges is not None and any(
        edge.treatment is EdgeTreatment.OPEN_RAILING
        for edge in (
            platform.edges.x_min,
            platform.edges.x_max,
            platform.edges.y_min,
            platform.edges.y_max,
        )
    ):
        return True
    return any(
        item.platform_id == platform_id and item.kind is PlatformStructureKind.GUARDRAIL
        for item in scene.platform_structure_observations
    )


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Add terrace/deck structure preservation to the existing fidelity chain.

    Only machine-readable Survey attributes become hard constraints here.  We do
    not parse prose to manufacture geometry.  The Scene may satisfy a certain
    structural observation either with resolved metric geometry or with an
    explicit non-metric ``PlatformStructureObservation`` when exact placement is
    still unknown.
    """
    issues = list(_validate_existing(survey, scene))
    scene_platform_ids = {item.id for item in scene.platforms}

    for observation in survey.observations:
        if observation.kind is not ObservationKind.PLATFORM:
            continue
        if observation.certainty is not Certainty.CERTAIN:
            continue
        if observation.id not in scene_platform_ids:
            # The existing validation chain owns the missing-platform diagnostic.
            continue

        if (
            "supports" in observation.attributes
            and observation.certainty_for_attribute("supports") is Certainty.CERTAIN
            and observation.attributes.get("supports")
            and not _has_preserved_support_structure(scene, observation.id)
        ):
            issues.append(
                SceneSurveyIssue(
                    code="certain_platform_support_structure_lost",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=observation.id,
                    message=(
                        f"La plateforme certaine {observation.id!r} possède une structure de support "
                        "certaine dans le Survey, mais la Scene ne conserve ni SupportPost métrisé ni "
                        "PlatformStructureObservation. Conservez l'existence de la structure même si "
                        "son nombre ou ses coordonnées exactes restent inconnus."
                    ),
                )
            )

        # Forward-compatible structured Survey vocabulary.  Current accepted
        # Surveys that mention a guardrail only in prose are intentionally not
        # promoted to a hard fact by this deterministic validator.
        if (
            "guardrail" in observation.attributes
            and observation.certainty_for_attribute("guardrail") is Certainty.CERTAIN
            and observation.attributes.get("guardrail")
            and not _has_preserved_guardrail(scene, observation.id)
        ):
            issues.append(
                SceneSurveyIssue(
                    code="certain_platform_guardrail_lost",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=observation.id,
                    message=(
                        f"La plateforme certaine {observation.id!r} possède un garde-corps certain "
                        "dans le Survey, mais la Scene ne conserve ni bord open_railing ni observation "
                        "structurelle de garde-corps."
                    ),
                )
            )

    return issues
