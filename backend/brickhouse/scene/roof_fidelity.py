"""Roof-shape fidelity checks across the Survey -> Scene boundary."""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import SceneRoofType
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import ArchitecturalScene
from .topology_fidelity import validate_scene_against_survey as _validate_existing


def _superseded_observation_ids(survey: ArchitecturalSurvey) -> set[str]:
    return {
        target_id
        for observation in survey.observations
        if isinstance((target_id := observation.attributes.get("refines_observation_id")), str)
        and target_id
    }


def _has_supported_gable_hypothesis(observation) -> bool:
    if observation.kind is not ObservationKind.ROOF:
        return False
    if (
        observation.attributes.get("roof_type") == "gable"
        and observation.certainty_for_attribute("roof_type") is not Certainty.UNPROVEN
    ):
        return True
    return (
        observation.attributes.get("facade_is_gable") is True
        and observation.certainty_for_attribute("facade_is_gable") is not Certainty.UNPROVEN
    )


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Preserve supported qualitative roof information without inventing metrics.

    A Survey is allowed to express a gable hypothesis through either ``roof_type``
    or the older/qualitative ``facade_is_gable`` attribute.  The Survey roof guard
    accepts both forms, so Scene validation must not silently degrade the latter to
    ``type='other'``.  This check does not require ridge direction or pitch: those
    may remain unknown and block LEGO projection honestly.
    """
    issues = list(_validate_existing(survey, scene))
    superseded = _superseded_observation_ids(survey)
    supported_gable = any(
        observation.id not in superseded and _has_supported_gable_hypothesis(observation)
        for observation in survey.observations
    )
    if supported_gable and not any(roof.type is SceneRoofType.GABLE for roof in scene.roofs):
        issues.append(
            SceneSurveyIssue(
                code="survey_gable_hypothesis_lost",
                severity=SceneSurveySeverity.ERROR,
                object_id=None,
                message=(
                    "Le Survey conserve une hypothèse de pignon/toiture gable soutenue, mais la Scene ne "
                    "contient aucun toit `gable`. Conservez l'hypothèse qualitative sans inventer la pente "
                    "ni l'axe; si ces métriques restent inconnues, laissez-les null et laissez M0 bloquer "
                    "plutôt que de dégrader silencieusement la toiture en `other`."
                ),
            )
        )
    return issues
