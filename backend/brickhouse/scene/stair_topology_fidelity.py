"""Preserve certain Survey stair-system topology across Survey -> Scene.

A Scene StairRun is metric. Survey may model either separate semantic run
observations or one semantic stair system with non-metric topology. The latter can
be metrically segmented only when Scene components explicitly preserve their parent
Survey stair-system identity; this module never invents coordinates or run counts.
"""

from __future__ import annotations

from brickhouse.survey import (
    ArchitecturalSurvey,
    Certainty,
    ObservationKind,
    analyze_survey_stair_topology,
)

from .platform_structure_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .wall_profile_scene import ArchitecturalScene


_PARENT_LINK_SUPERSEDED_CODES = {
    "certain_stair_missing",
    "certain_multiview_stair_not_geometrically_encoded",
    "certain_stair_not_geometrically_encoded",
}


def _required_minimum_runs(fact) -> int:
    topology = fact.topology
    required = topology.minimum_run_count or 1
    if topology.exact_run_count is not None:
        required = max(required, topology.exact_run_count)
    if topology.direction_change is True or topology.turning_node_kind is not None:
        required = max(required, 2)
    if topology.component_run_ids:
        required = max(required, len(topology.component_run_ids))
    return required


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Extend the fidelity chain with parent-aware non-collapse guards for multi-run stairs."""

    issues = list(_validate_existing(survey, scene))
    topology_report = analyze_survey_stair_topology(survey)
    scene_stair_ids = {item.id for item in scene.stairs}
    survey_observations = {item.id: item for item in survey.observations}

    links_by_system: dict[str, list[str]] = {}
    valid_linked_run_ids: set[str] = set()
    for link in scene.stair_system_links:
        observation = survey_observations.get(link.survey_stair_system_id)
        if observation is None:
            issues.append(
                SceneSurveyIssue(
                    code="stair_system_link_unknown_survey_observation",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=link.stair_run_id,
                    message=(
                        f"La volée Scene {link.stair_run_id!r} prétend provenir de l’observation Survey "
                        f"inconnue {link.survey_stair_system_id!r}."
                    ),
                )
            )
            continue
        if observation.kind is not ObservationKind.STAIR:
            issues.append(
                SceneSurveyIssue(
                    code="stair_system_link_source_not_stair",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=link.stair_run_id,
                    message=(
                        f"La volée Scene {link.stair_run_id!r} pointe vers {link.survey_stair_system_id!r}, "
                        "qui n’est pas une observation d’escalier dans le Survey."
                    ),
                )
            )
            continue
        links_by_system.setdefault(link.survey_stair_system_id, []).append(link.stair_run_id)
        valid_linked_run_ids.add(link.stair_run_id)

    # Older no-invention guards require every metric StairRun ID to equal a
    # Survey observation ID and separately report the parent stair as missing.
    # An explicit valid parent link is the provenance-preserving replacement for
    # those exact-ID assumptions. Suppress only those legacy identity diagnostics;
    # topology/count/geometry checks below remain strict.
    linked_system_ids = set(links_by_system)
    issues = [
        issue
        for issue in issues
        if not (
            issue.code == "scene_stair_not_in_survey"
            and issue.object_id in valid_linked_run_ids
        )
        and not (
            issue.code in _PARENT_LINK_SUPERSEDED_CODES
            and issue.object_id in linked_system_ids
        )
    ]

    for fact in topology_report.facts:
        if fact.certainty is not Certainty.CERTAIN or not fact.requires_multiple_scene_runs:
            continue

        explicit_component_ids = list(fact.topology.component_run_ids)
        if explicit_component_ids:
            missing = [component_id for component_id in explicit_component_ids if component_id not in scene_stair_ids]
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
            continue

        linked_component_ids = links_by_system.get(fact.observation_id, [])
        required = _required_minimum_runs(fact)
        exact = fact.topology.exact_run_count
        count_valid = len(linked_component_ids) >= required and (
            exact is None or len(linked_component_ids) == exact
        )
        if not count_valid:
            expectation = f"au moins {required}"
            if exact is not None:
                expectation = f"exactement {exact}"
            issues.append(
                SceneSurveyIssue(
                    code="multi_run_stair_topology_unresolved",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"L’escalier {fact.observation_id!r} est certainement multi-volées dans le Survey, "
                        f"mais la Scene ne fournit pas {expectation} volées métriques explicitement reliées "
                        "à ce système. Ne réduisez pas l’escalier à un seul start→end et n’inventez pas de "
                        "composants sans provenance."
                    ),
                )
            )

    return issues
