"""Final Survey -> Scene fidelity policy.

A Survey can prove that an architectural object exists without proving every
property of that object. This layer prevents lower-level validators from turning
plausible attributes into hard facts while keeping legacy Surveys compatible.
It also allows evidence-safe omission of certain exterior geometry whose hidden
continuation cannot be encoded without invention.
"""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import ArchitecturalScene
from .survey_structure_guard import validate_scene_against_survey as _validate_scene_against_survey
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity


_OMITTABLE_CERTAIN_GEOMETRY = {
    "certain_platform_missing": "certain_platform_not_geometrically_encoded",
    "certain_stair_missing": "certain_stair_not_geometrically_encoded",
}

# These attributes historically inherited the observation-level certainty. They
# directly drive topology/type constraints in Scene validation, so when a modern
# Survey explicitly marks one as plausible/unproven it must not be promoted back
# to a certain fact by a legacy validator.
_STRUCTURAL_ATTRIBUTE_KEYS = {
    ObservationKind.OPENING: ("semantic_type",),
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
    primitives remain fully validated.
    """
    validation_survey = _strict_claims_only(survey)
    issues = list(_validate_scene_against_survey(validation_survey, scene))
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
