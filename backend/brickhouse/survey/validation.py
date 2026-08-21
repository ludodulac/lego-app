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


def validate_survey_semantics(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Return semantic issues that Pydantic shape validation alone cannot catch."""
    issues: list[SurveyValidationIssue] = []

    for observation in survey.observations:
        attributes = observation.attributes

        if observation.kind is ObservationKind.OPENING:
            confirmed = bool(attributes.get("confirmed_by_user", False))
            semantic_role = attributes.get("semantic_role") or attributes.get("semantic_type")
            if confirmed and (not isinstance(semantic_role, str) or not semantic_role.strip()):
                issues.append(SurveyValidationIssue(
                    code="confirmed_opening_missing_semantic_role",
                    observation_id=observation.id,
                    message="User-confirmed opening requires a stable semantic_role; visual ambiguity may not erase its identity.",
                ))

            target_ownership = attributes.get("target_building_ownership")
            if observation.certainty in {Certainty.CERTAIN, Certainty.PLAUSIBLE}:
                if target_ownership == "unproven":
                    issues.append(SurveyValidationIssue(
                        code="opening_target_ownership_unproven",
                        observation_id=observation.id,
                        message="Opening ownership by the target building is unproven; mark the observation unproven or context until new evidence exists.",
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

    return issues


def validate_survey_extension(
    base: ArchitecturalSurvey,
    candidate: ArchitecturalSurvey,
) -> list[SurveyValidationIssue]:
    """Ensure an incremental Survey only adds knowledge and never rewrites validated facts.

    The extension contract is intentionally strict: every pre-existing photo,
    measurement, observation, frame definition and representation policy must
    survive byte-for-byte at the model level. New photos and observations may
    be appended. Corrections to already validated facts belong to a separate,
    explicit correction workflow rather than an extension pass.
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
        if photo.photo_index not in {item.photo_index for item in base.photos} and photo.photo_index <= base_max_photo:
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

    issues.extend(validate_survey_semantics(candidate))
    return issues
