"""Semantic validation helpers for ArchitecturalSurvey."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ArchitecturalSurvey, Certainty, ObservationKind


@dataclass(frozen=True)
class SurveyValidationIssue:
    code: str
    observation_id: str | None
    message: str
    severity: str = "error"


_ARCHITECTURAL_KIND_BY_TAG = {
    "volume": ObservationKind.VOLUME,
    "platform": ObservationKind.PLATFORM,
    "stair": ObservationKind.STAIR,
}


def _valid_positive_rank(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 1


def _validate_refinement_semantics(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Validate append-only refinements of uncertain observations.

    New photos must be able to resolve a previous plausible/unproven hypothesis
    without erasing its provenance. The old observation therefore stays in the
    Survey and a new observation may point to it through
    attributes.refines_observation_id. Certain or user-confirmed facts are never
    refinable through this mechanism; corrections to those require the explicit
    correction workflow.
    """
    issues: list[SurveyValidationIssue] = []
    observations = {item.id: item for item in survey.observations}

    for observation in survey.observations:
        target_id = observation.attributes.get("refines_observation_id")
        if target_id is None:
            continue
        if not isinstance(target_id, str) or not target_id.strip():
            issues.append(SurveyValidationIssue(
                code="invalid_refinement_target",
                observation_id=observation.id,
                message="attributes.refines_observation_id doit contenir l’id non vide d’une observation antérieure.",
            ))
            continue
        if target_id == observation.id:
            issues.append(SurveyValidationIssue(
                code="self_refinement",
                observation_id=observation.id,
                message="Une observation ne peut pas se raffiner elle-même.",
            ))
            continue
        target = observations.get(target_id)
        if target is None:
            issues.append(SurveyValidationIssue(
                code="refinement_target_missing",
                observation_id=observation.id,
                message=f"L’observation raffinée {target_id!r} n’existe pas dans ce Survey.",
            ))
            continue
        if target.kind is not observation.kind:
            issues.append(SurveyValidationIssue(
                code="refinement_kind_changed",
                observation_id=observation.id,
                message=(
                    f"Une observation de type {observation.kind.value!r} ne peut pas raffiner "
                    f"une observation de type {target.kind.value!r}."
                ),
            ))
        if target.certainty is Certainty.CERTAIN or bool(target.attributes.get("confirmed_by_user", False)):
            issues.append(SurveyValidationIssue(
                code="certain_observation_cannot_be_refined",
                observation_id=observation.id,
                message=(
                    f"L’observation {target_id!r} est déjà certaine ou confirmée par l’utilisateur. "
                    "Une extension photo ne peut pas la réécrire ; utilisez le workflow de correction explicite en cas d’erreur."
                ),
            ))
        previous_photos = {item.photo_index for item in target.evidence}
        if not any(item.photo_index not in previous_photos for item in observation.evidence):
            issues.append(SurveyValidationIssue(
                code="refinement_without_new_evidence",
                observation_id=observation.id,
                message=(
                    f"Le raffinement de {target_id!r} doit citer au moins une preuve photo qui n’était pas déjà "
                    "dans l’observation raffinée."
                ),
            ))

    # Refinement chains are allowed (unproven -> plausible -> certain), but cycles are not.
    for observation in survey.observations:
        seen = {observation.id}
        current = observation
        while True:
            target_id = current.attributes.get("refines_observation_id")
            if not isinstance(target_id, str) or target_id not in observations:
                break
            if target_id in seen:
                issues.append(SurveyValidationIssue(
                    code="refinement_cycle",
                    observation_id=observation.id,
                    message="La chaîne de raffinement contient une boucle ; elle doit rester chronologique et append-only.",
                ))
                break
            seen.add(target_id)
            current = observations[target_id]

    return issues


def validate_survey_semantics(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Return semantic issues that Pydantic shape validation alone cannot catch."""
    issues: list[SurveyValidationIssue] = []

    for observation in survey.observations:
        attributes = observation.attributes
        target_ownership = attributes.get("target_building_ownership")
        architectural_kind = attributes.get("architectural_kind")

        if observation.kind is ObservationKind.CONTEXT and target_ownership == "proven":
            issues.append(SurveyValidationIssue(
                code="target_building_element_downgraded_to_context",
                observation_id=observation.id,
                message="Un élément dont l’appartenance au bâtiment cible est prouvée ne peut pas être classé context. Utilisez son kind architectural natif ou signalez une limitation de contrat.",
            ))

        expected_kind = _ARCHITECTURAL_KIND_BY_TAG.get(architectural_kind)
        if expected_kind is not None and observation.kind is not expected_kind:
            issues.append(SurveyValidationIssue(
                code="architectural_kind_mismatch",
                observation_id=observation.id,
                message=f"L’observation déclare attributes.architectural_kind={architectural_kind!r} mais kind={observation.kind.value!r}. Elle doit utiliser kind={expected_kind.value!r}.",
            ))

        if observation.kind is ObservationKind.OPENING:
            confirmed = bool(attributes.get("confirmed_by_user", False))
            semantic_role = attributes.get("semantic_role") or attributes.get("semantic_type")
            if confirmed and (not isinstance(semantic_role, str) or not semantic_role.strip()):
                issues.append(SurveyValidationIssue(
                    code="confirmed_opening_missing_semantic_role",
                    observation_id=observation.id,
                    message="User-confirmed opening requires a stable semantic_role; visual ambiguity may not erase its identity.",
                ))

            if observation.certainty in {Certainty.CERTAIN, Certainty.PLAUSIBLE}:
                if target_ownership == "unproven":
                    issues.append(SurveyValidationIssue(
                        code="opening_target_ownership_unproven",
                        observation_id=observation.id,
                        message="Opening ownership by the target building is unproven; mark the observation unproven or context until new evidence exists.",
                    ))

            for field in ("facade_horizontal_rank", "facade_vertical_rank"):
                value = attributes.get(field)
                if value is not None and not _valid_positive_rank(value):
                    issues.append(SurveyValidationIssue(
                        code="invalid_opening_layout_rank",
                        observation_id=observation.id,
                        message=(
                            f"{field} doit être un entier positif 1..N lorsqu’il est renseigné. "
                            "Ces rangs sont qualitatifs et ne doivent pas contenir de mètres, pixels ou texte libre."
                        ),
                    ))

        if observation.kind is ObservationKind.ROOF:
            roof_edge = attributes.get("roof_edge_type")
            if observation.facade is not None and observation.facade.value == "front":
                gable_end = attributes.get("facade_roof_relationship") == "gable_end"
                if gable_end and roof_edge == "eave_across_facade":
                    issues.append(SurveyValidationIssue(
                        code="gable_eave_terminology_conflict",
                        observation_id=observation.id,
                        message="A gable-end front facade cannot simultaneously have a horizontal eave across that facade; use rake/gable-edge terminology.",
                    ))

    issues.extend(_validate_refinement_semantics(survey))
    return issues


def validate_survey_extension(
    base: ArchitecturalSurvey,
    candidate: ArchitecturalSurvey,
) -> list[SurveyValidationIssue]:
    """Ensure an incremental Survey only adds knowledge and never rewrites validated facts.

    The extension contract is intentionally strict: every pre-existing photo,
    measurement, observation, relation, frame definition and representation policy
    must survive byte-for-byte at the model level. New photos, observations and
    relations may be appended. Uncertain hypotheses can be refined only through a
    new append-only observation carrying attributes.refines_observation_id.
    Corrections to certain validated facts belong to the explicit correction
    workflow rather than an extension pass.
    """
    issues: list[SurveyValidationIssue] = []

    if candidate.id != base.id:
        issues.append(SurveyValidationIssue(
            code="survey_extension_id_changed",
            observation_id=None,
            message="Le Survey étendu doit conserver exactement le même id que le Survey validé de départ.",
        ))
    if candidate.canonical_frame != base.canonical_frame:
        issues.append(SurveyValidationIssue(
            code="survey_extension_frame_changed",
            observation_id=None,
            message="Le repère canonique du Survey validé ne peut pas être modifié pendant une extension.",
        ))
    if candidate.known_measurements != base.known_measurements:
        issues.append(SurveyValidationIssue(
            code="survey_extension_measurements_changed",
            observation_id=None,
            message="Les mesures connues du Survey validé doivent être conservées exactement pendant une extension.",
        ))
    if candidate.representation_policy != base.representation_policy:
        issues.append(SurveyValidationIssue(
            code="survey_extension_policy_changed",
            observation_id=None,
            message="La politique de représentation du Survey validé ne peut pas être modifiée pendant une extension.",
        ))

    candidate_photos = {photo.photo_index: photo for photo in candidate.photos}
    base_photo_indexes = {photo.photo_index for photo in base.photos}
    for photo in base.photos:
        if photo.photo_index not in candidate_photos:
            issues.append(SurveyValidationIssue(
                code="survey_extension_photo_removed",
                observation_id=None,
                message=f"La photo {photo.photo_index} du Survey validé a disparu du Survey étendu.",
            ))
        elif candidate_photos[photo.photo_index] != photo:
            issues.append(SurveyValidationIssue(
                code="survey_extension_photo_changed",
                observation_id=None,
                message=f"La description/orientation de la photo {photo.photo_index} a été modifiée. Une extension doit la conserver exactement.",
            ))

    base_max_photo = max(photo.photo_index for photo in base.photos)
    for photo in candidate.photos:
        if photo.photo_index not in base_photo_indexes and photo.photo_index <= base_max_photo:
            issues.append(SurveyValidationIssue(
                code="survey_extension_photo_index_reused",
                observation_id=None,
                message=f"La nouvelle photo {photo.photo_index} réutilise un index ancien. Les nouvelles photos doivent commencer après {base_max_photo}.",
            ))

    candidate_observations = {observation.id: observation for observation in candidate.observations}
    for observation in base.observations:
        current = candidate_observations.get(observation.id)
        if current is None:
            issues.append(SurveyValidationIssue(
                code="survey_extension_observation_removed",
                observation_id=observation.id,
                message=f"L’observation validée '{observation.id}' a disparu du Survey étendu.",
            ))
        elif current != observation:
            issues.append(SurveyValidationIssue(
                code="survey_extension_observation_changed",
                observation_id=observation.id,
                message=f"L’observation validée '{observation.id}' a été modifiée. Une extension doit conserver exactement les observations existantes et seulement en ajouter de nouvelles.",
            ))

    candidate_relations = {relation.id: relation for relation in candidate.relations}
    for relation in base.relations:
        current = candidate_relations.get(relation.id)
        if current is None:
            issues.append(SurveyValidationIssue(
                code="survey_extension_relation_removed",
                observation_id=None,
                message=f"La relation validée '{relation.id}' a disparu du Survey étendu.",
            ))
        elif current != relation:
            issues.append(SurveyValidationIssue(
                code="survey_extension_relation_changed",
                observation_id=None,
                message=f"La relation validée '{relation.id}' a été modifiée. Une extension doit la conserver exactement et seulement ajouter de nouvelles relations.",
            ))

    if len(candidate.photos) <= len(base.photos):
        issues.append(SurveyValidationIssue(
            code="survey_extension_no_new_photo",
            observation_id=None,
            message="Le Survey candidat n’ajoute aucune nouvelle photo ; ce n’est pas une extension.",
        ))

    if len(candidate.observations) < len(base.observations):
        issues.append(SurveyValidationIssue(
            code="survey_extension_observation_count_decreased",
            observation_id=None,
            message="Le nombre d’observations ne peut pas diminuer pendant une extension.",
        ))
    if len(candidate.relations) < len(base.relations):
        issues.append(SurveyValidationIssue(
            code="survey_extension_relation_count_decreased",
            observation_id=None,
            message="Le nombre de relations validées ne peut pas diminuer pendant une extension.",
        ))

    issues.extend(validate_survey_semantics(candidate))
    return issues
