"""Final Survey -> Scene fidelity policy.

This module resolves an important distinction that the lower-level validators
cannot express on their own: a Survey can prove that an exterior platform or
stair exists without proving enough hidden geometry to encode a complete,
connected Scene primitive.

Rendered primitives remain subject to all strict connectivity and no-invention
guards.  The only relaxation here is that omission of a *certain* platform or
stair is reported as an explicit warning rather than an error.  This lets the
reconstruction follow the prompt's rule "omit rather than invent" when the
hidden connection cannot be supported by evidence.
"""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey

from .models import ArchitecturalScene
from .survey_structure_guard import validate_scene_against_survey as _validate_scene_against_survey
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity


_OMITTABLE_CERTAIN_GEOMETRY = {
    "certain_platform_missing": "certain_platform_not_geometrically_encoded",
    "certain_stair_missing": "certain_stair_not_geometrically_encoded",
}


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Validate fidelity without forcing hidden exterior geometry to be invented.

    A certain Survey observation establishes architectural existence.  It does
    not necessarily establish enough metric geometry to create a complete
    Platform/StairRun satisfying Scene connectivity.  In that specific case the
    Scene may omit the primitive; the omission remains visible to callers as a
    warning and should be explained in ``scene.notes`` by the reconstruction
    stage.

    This does *not* weaken validation of a platform/stair that is actually
    rendered: invented primitives, unproven promotion, confidence discipline,
    edge semantics and geometric connectivity are still enforced by the
    underlying validators.
    """
    issues = list(_validate_scene_against_survey(survey, scene))
    result: list[SceneSurveyIssue] = []

    for issue in issues:
        replacement_code = _OMITTABLE_CERTAIN_GEOMETRY.get(issue.code)
        if replacement_code is None:
            result.append(issue)
            continue
        result.append(
            SceneSurveyIssue(
                code=replacement_code,
                severity=SceneSurveySeverity.WARNING,
                object_id=issue.object_id,
                message=(
                    f"{issue.message} La Scene peut omettre cette géométrie plutôt que "
                    "d'inventer une portion ou une connexion occultée; documentez la "
                    "limitation dans scene.notes."
                ),
            )
        )

    return result
