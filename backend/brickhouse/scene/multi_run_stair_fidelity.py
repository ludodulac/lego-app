"""Preserve realized multi-run stair continuity across Survey -> Scene."""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty, analyze_survey_stair_topology

from .multi_run_stair_geometry import analyze_multi_run_stair_geometry
from .ownership_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .wall_profile_scene import ArchitecturalScene


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Extend fidelity with deterministic multi-run continuity/turn checks."""
    issues = list(_validate_existing(survey, scene))
    topology_by_id = {
        item.observation_id: item
        for item in analyze_survey_stair_topology(survey).facts
        if item.certainty is Certainty.CERTAIN
    }

    for fact in analyze_multi_run_stair_geometry(survey, scene).facts:
        topology_fact = topology_by_id.get(fact.observation_id)
        if topology_fact is None or not fact.all_components_present:
            # Missing components are already reported by the BH-171 fidelity gate.
            continue

        if fact.connected is False:
            issues.append(SceneSurveyIssue(
                code="multi_run_stair_components_disconnected",
                severity=SceneSurveySeverity.ERROR,
                object_id=fact.observation_id,
                message=(
                    f"Les volées certaines de l’escalier {fact.observation_id!r} existent dans la Scene "
                    "mais leurs extrémités ne forment pas un système connecté dans la tolérance canonique. "
                    "Ne comblez pas l’écart avec un palier ou des coordonnées inventés."
                ),
            ))
            continue

        if fact.spanning_path_exists is False:
            issues.append(SceneSurveyIssue(
                code="multi_run_stair_no_continuous_path",
                severity=SceneSurveySeverity.ERROR,
                object_id=fact.observation_id,
                message=(
                    f"Les volées de {fact.observation_id!r} se touchent, mais aucune chaîne continue ne peut "
                    "parcourir tous les composants une seule fois. La Scene ne réalise donc pas une séquence "
                    "d’escalier cohérente."
                ),
            ))
            continue

        expected_change = topology_fact.topology.direction_change
        if expected_change is True:
            if fact.direction_change_realized is False:
                issues.append(SceneSurveyIssue(
                    code="multi_run_stair_direction_change_not_realized",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"Le Survey établit un changement de direction pour {fact.observation_id!r}, mais les "
                        "volées métriques connectées restent collinéaires. Plusieurs StairRun ne suffisent pas "
                        "à réaliser un escalier tournant."
                    ),
                ))
            elif fact.direction_change_realized is None:
                issues.append(SceneSurveyIssue(
                    code="multi_run_stair_direction_change_unresolved",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"Le changement de direction certain de {fact.observation_id!r} ne peut pas être "
                        "vérifié parce qu’au moins une volée métrique est dégénérée. Gardez la géométrie "
                        "non résolue plutôt que d’en faire une preuve."
                    ),
                ))
        elif expected_change is False and fact.direction_change_realized is True:
            issues.append(SceneSurveyIssue(
                code="multi_run_stair_unexpected_direction_change",
                severity=SceneSurveySeverity.ERROR,
                object_id=fact.observation_id,
                message=(
                    f"Le Survey établit l’absence de changement de direction pour {fact.observation_id!r}, "
                    "mais la Scene introduit une jonction non collinéaire."
                ),
            ))

    return issues
