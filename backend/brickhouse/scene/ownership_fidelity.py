"""Preserve Survey target-vs-context ownership across Survey -> Scene.

ArchitecturalScene contains target reconstruction primitives.  Therefore an
observation known to belong to external context must not reappear as a target
Scene object, and an observation whose ownership is still uncertain must not be
silently metrified into target geometry.
"""

from __future__ import annotations

from brickhouse.survey import (
    ArchitecturalSurvey,
    Certainty,
    SubjectOwnership,
    analyze_subject_ownership,
)

from .stair_topology_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .wall_profile_scene import ArchitecturalScene


def _scene_object_ids(scene: ArchitecturalScene) -> set[str]:
    return {
        item.id
        for item in [
            *scene.volumes,
            *scene.openings,
            *scene.roofs,
            *scene.chimneys,
            *scene.platforms,
            *scene.stairs,
            *scene.equipment,
        ]
    }


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Extend the fidelity chain with explicit ownership anti-promotion guards."""

    issues = list(_validate_existing(survey, scene))
    report = analyze_subject_ownership(survey)
    scene_ids = _scene_object_ids(scene)

    for fact in report.facts:
        if fact.observation_id not in scene_ids:
            continue

        if fact.certainty is not Certainty.CERTAIN:
            issues.append(
                SceneSurveyIssue(
                    code="uncertain_subject_ownership_metrified",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"L’observation {fact.observation_id!r} a une propriété subject_ownership "
                        f"{fact.ownership.value!r} seulement {fact.certainty.value!r}, mais elle a été "
                        "métrifiée comme primitive de la Scene cible. Résolvez d’abord l’appartenance "
                        "depuis les preuves ; ne transformez pas une attribution incertaine en géométrie."
                    ),
                )
            )
            continue

        if fact.ownership is SubjectOwnership.EXTERNAL_CONTEXT:
            issues.append(
                SceneSurveyIssue(
                    code="external_context_object_reconstructed_as_target",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message=(
                        f"L’observation {fact.observation_id!r} appartient certainement au contexte "
                        "extérieur mais réapparaît comme primitive de la Scene cible. Un bâtiment voisin, "
                        "sa cheminée, ses ouvertures ou ses équipements ne doivent pas être absorbés par "
                        "la reconstruction du bâtiment étudié."
                    ),
                )
            )
        elif fact.ownership is SubjectOwnership.UNRESOLVED:
            # Defensive branch: Survey validation already rejects certain+unresolved,
            # but Scene fidelity remains safe if called on a non-validated Survey.
            issues.append(
                SceneSurveyIssue(
                    code="unresolved_subject_ownership_metrified",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=fact.observation_id,
                    message="Un objet à appartenance non résolue ne peut pas devenir une primitive cible métrique.",
                )
            )

    return issues
