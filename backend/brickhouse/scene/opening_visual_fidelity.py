"""Opening-detail fidelity on top of the core Survey -> Scene validator."""
from __future__ import annotations

from brickhouse.building import OpeningType
from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .fidelity_validation import validate_scene_against_survey as _validate_core_fidelity
from .models import ArchitecturalScene
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity


def _observed_window_trim_issues(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Keep explicitly observed sill/surround facts without inventing joinery.

    OpeningVisualDescription has no per-field certainty map yet, so this guard is
    deliberately narrow: it only treats visual details on a CERTAIN opening as
    required when the corresponding visual field is explicitly populated and the
    resulting Scene opening is a window (the only opening type whose current
    Scene schema can encode sill/surround metadata).
    """
    scene_openings = {opening.id: opening for opening in scene.openings}
    issues: list[SceneSurveyIssue] = []

    for observation in survey.observations:
        if (
            observation.kind is not ObservationKind.OPENING
            or observation.certainty is not Certainty.CERTAIN
            or observation.opening_visual is None
        ):
            continue
        opening = scene_openings.get(observation.id)
        if opening is None or opening.type is not OpeningType.WINDOW:
            continue

        visual = observation.opening_visual
        if visual.sill is not None and opening.has_sill is not True:
            issues.append(
                SceneSurveyIssue(
                    code="opening_sill_lost",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=observation.id,
                    message=(
                        f"L'ouverture {observation.id!r} possède un appui explicitement observé dans le Survey, "
                        "mais SceneOpening.has_sill ne le conserve pas."
                    ),
                )
            )

        surround_observed = visual.surround_material is not None or visual.surround_color is not None
        if surround_observed and opening.has_decorative_surround is not True:
            issues.append(
                SceneSurveyIssue(
                    code="opening_surround_lost",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=observation.id,
                    message=(
                        f"L'ouverture {observation.id!r} possède un encadrement extérieur explicitement observé "
                        "dans le Survey, mais SceneOpening.has_decorative_surround ne le conserve pas."
                    ),
                )
            )

    return issues


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Run the core fidelity checks plus explicit opening-trim preservation."""
    issues = list(_validate_core_fidelity(survey, scene))
    issues.extend(_observed_window_trim_issues(survey, scene))
    return issues
