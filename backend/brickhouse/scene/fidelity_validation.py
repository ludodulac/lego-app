"""Final Survey -> Scene fidelity policy.

A Survey can prove that an architectural object exists without proving every
property of that object. This layer prevents lower-level validators from turning
plausible attributes into hard facts while keeping legacy Surveys compatible.
It also allows evidence-safe omission of certain exterior geometry whose hidden
continuation cannot be encoded without invention.
"""
from __future__ import annotations

from itertools import combinations

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import ArchitecturalScene
from .survey_structure_guard import validate_scene_against_survey as _validate_scene_against_survey
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity


_OMITTABLE_CERTAIN_GEOMETRY = {
    "certain_platform_missing": "certain_platform_not_geometrically_encoded",
    "certain_stair_missing": "certain_stair_not_geometrically_encoded",
}

# These attributes historically inherited the observation-level certainty. They
# directly drive topology/type/layout constraints in Scene validation, so when a
# modern Survey explicitly marks one as plausible/unproven it must not be
# promoted back to a certain fact by a legacy validator.
_STRUCTURAL_ATTRIBUTE_KEYS = {
    ObservationKind.OPENING: (
        "semantic_type",
        "facade_horizontal_rank",
        "facade_vertical_rank",
    ),
    ObservationKind.ROOF: ("facade_is_gable", "front_is_gable"),
    ObservationKind.TERRAIN: ("slope_direction",),
}


def _strict_claims_only(survey: ArchitecturalSurvey) -> ArchitecturalSurvey:
    """Hide explicitly non-certain structural attributes from strict validators.

    Missing ``attribute_certainty`` entries retain historical behavior exactly.
    Only a key explicitly present in that map with plausible/unproven certainty
    relaxes the corresponding attribute-level constraint.
    """
    observations = []
    changed = False
    for observation in survey.observations:
        keys = _STRUCTURAL_ATTRIBUTE_KEYS.get(observation.kind, ())
        remove = {
            key
            for key in keys
            if key in observation.attributes
            and key in observation.attribute_certainty
            and observation.attribute_certainty[key] is not Certainty.CERTAIN
        }
        if not remove:
            observations.append(observation)
            continue
        changed = True
        attributes = {
            key: value for key, value in observation.attributes.items() if key not in remove
        }
        attribute_certainty = {
            key: value
            for key, value in observation.attribute_certainty.items()
            if key not in remove
        }
        observations.append(
            observation.model_copy(
                update={
                    "attributes": attributes,
                    "attribute_certainty": attribute_certainty,
                }
            )
        )
    if not changed:
        return survey
    return survey.model_copy(update={"observations": observations})


def _superseded_observation_ids(survey: ArchitecturalSurvey) -> set[str]:
    return {
        target_id
        for observation in survey.observations
        if isinstance((target_id := observation.attributes.get("refines_observation_id")), str)
        and target_id
    }


def _certain_roof_existence_issues(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """A certainly observed roof must survive into Scene even if its shape is unknown."""
    if scene.roofs:
        return []

    superseded = _superseded_observation_ids(survey)
    certain_roofs = [
        observation
        for observation in survey.observations
        if observation.kind is ObservationKind.ROOF
        and observation.certainty is Certainty.CERTAIN
        and observation.id not in superseded
    ]
    if not certain_roofs:
        return []

    return [
        SceneSurveyIssue(
            code="certain_roof_missing",
            severity=SceneSurveySeverity.ERROR,
            object_id=observation.id,
            message=(
                f"La toiture certaine {observation.id!r} a disparu de la Scene. "
                "Conservez son existence même si sa forme, son axe ou sa pente restent inconnus."
            ),
        )
        for observation in certain_roofs
    ]


def _opening_layout_order_issues(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Preserve certain qualitative opening order without inventing metric spacing."""
    scene_openings = {opening.id: opening for opening in scene.openings}
    observations = [
        observation
        for observation in survey.observations
        if observation.kind is ObservationKind.OPENING
        and observation.certainty is Certainty.CERTAIN
        and observation.facade is not None
        and observation.id in scene_openings
    ]
    issues: list[SceneSurveyIssue] = []

    for first, second in combinations(observations, 2):
        if first.facade is not second.facade:
            continue
        first_scene = scene_openings[first.id]
        second_scene = scene_openings[second.id]

        horizontal_first = first.attributes.get("facade_horizontal_rank")
        horizontal_second = second.attributes.get("facade_horizontal_rank")
        if (
            isinstance(horizontal_first, int)
            and not isinstance(horizontal_first, bool)
            and isinstance(horizontal_second, int)
            and not isinstance(horizontal_second, bool)
            and horizontal_first != horizontal_second
        ):
            first_center = first_scene.offset_horizontal + first_scene.width / 2
            second_center = second_scene.offset_horizontal + second_scene.width / 2
            order_holds = (
                first_center < second_center
                if horizontal_first < horizontal_second
                else first_center > second_center
            )
            if not order_holds:
                issues.append(
                    SceneSurveyIssue(
                        code="opening_horizontal_order_drift",
                        severity=SceneSurveySeverity.ERROR,
                        object_id=second.id,
                        message=(
                            f"Les ouvertures {first.id!r} et {second.id!r} ont inversé leur ordre horizontal "
                            f"certain sur la façade {first.facade.value}. Les rangs qualitatifs imposent "
                            "l'ordre gauche→droite, pas une distance métrique."
                        ),
                    )
                )

        vertical_first = first.attributes.get("facade_vertical_rank")
        vertical_second = second.attributes.get("facade_vertical_rank")
        if (
            isinstance(vertical_first, int)
            and not isinstance(vertical_first, bool)
            and isinstance(vertical_second, int)
            and not isinstance(vertical_second, bool)
            and vertical_first != vertical_second
        ):
            first_center = first_scene.offset_vertical + first_scene.height / 2
            second_center = second_scene.offset_vertical + second_scene.height / 2
            order_holds = (
                first_center < second_center
                if vertical_first < vertical_second
                else first_center > second_center
            )
            if not order_holds:
                issues.append(
                    SceneSurveyIssue(
                        code="opening_vertical_order_drift",
                        severity=SceneSurveySeverity.ERROR,
                        object_id=second.id,
                        message=(
                            f"Les ouvertures {first.id!r} et {second.id!r} ont inversé leur ordre vertical "
                            f"certain sur la façade {first.facade.value}. Les rangs qualitatifs imposent "
                            "l'ordre bas→haut, pas une hauteur métrique."
                        ),
                    )
                )

    return issues


def _omission_is_documented(scene: ArchitecturalScene, object_id: str | None) -> bool:
    """Require an explicit object-level audit trail before relaxing a missing primitive."""
    if not object_id or not scene.notes:
        return False
    return object_id.casefold() in scene.notes.casefold()


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Validate fidelity without promoting uncertain properties or hidden geometry.

    Object existence and attribute certainty are independent. Strict historical
    guards see only explicitly certain modern structural attributes, while legacy
    Surveys keep their prior semantics. Certain Platform/StairRun observations
    may also be omitted when hidden geometry would otherwise have to be invented,
    but only when ``scene.notes`` names that exact Survey object. Rendered
    primitives remain fully validated. A certainly observed roof is never
    omittable: Scene can preserve it with unknown geometry, but cannot erase it.
    Certain qualitative opening ranks preserve ordering while remaining entirely
    non-metric.
    """
    validation_survey = _strict_claims_only(survey)
    issues = list(_validate_scene_against_survey(validation_survey, scene))
    issues.extend(_certain_roof_existence_issues(validation_survey, scene))
    issues.extend(_opening_layout_order_issues(validation_survey, scene))
    result: list[SceneSurveyIssue] = []

    for issue in issues:
        replacement_code = _OMITTABLE_CERTAIN_GEOMETRY.get(issue.code)
        if replacement_code is None or not _omission_is_documented(scene, issue.object_id):
            result.append(issue)
            continue
        result.append(
            SceneSurveyIssue(
                code=replacement_code,
                severity=SceneSurveySeverity.WARNING,
                object_id=issue.object_id,
                message=(
                    f"{issue.message} L'omission est explicitement tracée dans scene.notes; "
                    "elle est acceptée plutôt que d'inventer une portion ou une connexion occultée."
                ),
            )
        )

    return result
