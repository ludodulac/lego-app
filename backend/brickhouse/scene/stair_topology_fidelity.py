"""Preserve certain Survey stair-system topology across Survey -> Scene.

A Scene StairRun is metric.  When the Survey only proves that an architectural
stair has multiple runs, the honest result is therefore an unresolved fidelity
error until separately evidenced component runs can be metrified.  This module
never splits a stair or invents coordinates to satisfy the gate.
"""

from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty, analyze_survey_stair_topology

from .platform_structure_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .wall_profile_scene import ArchitecturalScene


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Extend the fidelity chain with a non-collapse gate for multi-run stairs."""

    issues = list(_validate_existing(survey, scene))
    topology_report = analyze_survey_stair_topology(survey)
    scene_stair_ids = {item.id for item in scene.stairs}

    for fact in topology_report.facts:
        if fact.certainty is not Certainty.CERTAIN or not fact.requires_multiple_scene_runs:
            continue

        component_ids = fact.topology.component_run_ids
        if not component_ids:
            issues.append(
                SceneSurveyIssue(
                    code="multi_run_stair_topology_unresolved",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"L’escalier {fact.observation_id!r} est certainement multi-volées dans le Survey, "
                        "mais ses volées n’ont pas encore d’identités sémantiques séparées. Ne le réduisez "
                        "pas à un StairRun start→end et n’inventez pas de coordonnées : résolvez d’abord "
                        "les composants depuis les preuves."
                    ),
                )
            )
            continue

        missing = [component_id for component_id in component_ids if component_id not in scene_stair_ids]
        if missing:
            issues.append(
                SceneSurveyIssue(
                    code="multi_run_stair_component_lost",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"L’escalier multi-volées {fact.observation_id!r} perd des volées certaines dans "
                        f"la Scene : {', '.join(repr(item) for item in missing)}. Chaque composant métrisé "
                        "doit conserver son ID Survey ; sinon la topologie reste non résolue."
                    ),
                )
            )

    return issues
