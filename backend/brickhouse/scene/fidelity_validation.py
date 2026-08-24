"""Final Survey -> Scene fidelity policy.

A Survey can prove that an exterior platform or stair exists without proving
enough hidden geometry to encode a complete connected Scene primitive. Rendered
primitives stay under the strict connectivity/no-invention guards. A missing
certain platform/stair is relaxed only when the Scene explicitly records that
specific omitted Survey object in ``notes``.
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


def _omission_is_documented(scene: ArchitecturalScene, object_id: str | None) -> bool:
    """Require an explicit object-level audit trail before relaxing a missing primitive."""
    if not object_id or not scene.notes:
        return False
    return object_id.casefold() in scene.notes.casefold()


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Validate fidelity without forcing hidden exterior geometry to be invented.

    Certain architectural existence is distinct from complete metric geometry.
    A certain Platform/StairRun may therefore be omitted when encoding it would
    require an unsupported hidden continuation, but only if ``scene.notes`` names
    that exact Survey object. An undocumented omission remains an error.

    This does not weaken validation of rendered primitives: invented primitives,
    unproven promotion, confidence discipline, edge semantics and geometric
    connectivity are still enforced by the underlying validators.
    """
    issues = list(_validate_scene_against_survey(survey, scene))
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
