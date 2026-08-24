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

_ARCHITECTURAL_KIND_BY_TAG={"volume":ObservationKind.VOLUME,"platform":ObservationKind.PLATFORM,"stair":ObservationKind.STAIR}
def _valid_positive_rank(value)->bool: return not isinstance(value,bool) and isinstance(value,int) and value>=1

def _meaningful_roof_shape_hypothesis(attributes: dict) -> bool:
    for name in ("roof_type", "facade_roof_relationship", "roof_edge_type"):
        value=attributes.get(name)
        if isinstance(value,str) and value.strip(): return True
    return isinstance(attributes.get("facade_is_gable"), bool)

def _validate_refinement_semantics(survey: ArchitecturalSurvey)->list[SurveyValidationIssue]:
    issues=[]; observations={item.id:item for item in survey.observations}
    for observation in survey.observations:
        target_id=observation.attributes.get("refines_observation_id")
        if target_id is None: continue
        if not isinstance(target_id,str) or not target_id.strip(): issues.append(SurveyValidationIssue("invalid_refinement_target",observation.id,"attributes.refines_observation_id doit contenir l’id non vide d’une observation antérieure.")); continue
        if target_id==observation.id: issues.append(SurveyValidationIssue("self_refinement",observation.id,"Une observation ne peut pas se raffiner elle-même.")); continue
        target=observations.get(target_id)
        if target is None: issues.append(SurveyValidationIssue("refinement_target_missing",observation.id,f"L’observation raffinée {target_id!r} n’existe pas dans ce Survey.")); continue
        if target.kind is not observation.kind: issues.append(SurveyValidationIssue("refinement_kind_changed",observation.id,f"Une observation de type {observation.kind.value!r} ne peut pas raffiner une observation de type {target.kind.value!r}."))
        if target.certainty is Certainty.CERTAIN or bool(target.attributes.get("confirmed_by_user",False)): issues.append(SurveyValidationIssue("certain_observation_cannot_be_refined",observation.id,f"L’observation {target_id!r} est déjà certaine ou confirmée par l’utilisateur. Une extension photo ne peut pas la réécrire ; utilisez le workflow de correction explicite en cas d’erreur."))
        previous_photos={item.photo_index for item in target.evidence}
        if not any(item.photo_index not in previous_photos for item in observation.evidence): issues.append(SurveyValidationIssue("refinement_without_new_evidence",observation.id,f"Le raffinement de {target_id!r} doit citer au moins une preuve photo qui n’était pas déjà dans l’observation raffinée."))
    for observation in survey.observations:
        seen={observation.id}; current=observation
        while True:
            target_id=current.attributes.get("refines_observation_id")
            if not isinstance(target_id,str) or target_id not in observations: break
            if target_id in seen: issues.append(SurveyValidationIssue("refinement_cycle",observation.id,"La chaîne de raffinement contient une boucle ; elle doit rester chronologique et append-only.")); break
            seen.add(target_id); current=observations[target_id]
    return issues

def validate_survey_semantics(survey: ArchitecturalSurvey)->list[SurveyValidationIssue]:
    issues=[]
    for observation in survey.observations:
        attributes=observation.attributes; target_ownership=attributes.get("target_building_ownership"); architectural_kind=attributes.get("architectural_kind")
        if observation.kind is ObservationKind.CONTEXT and target_ownership=="proven": issues.append(SurveyValidationIssue("target_building_element_downgraded_to_context",observation.id,"Un élément dont l’appartenance au bâtiment cible est prouvée ne peut pas être classé context. Utilisez son kind architectural natif ou signalez une limitation de contrat."))
        expected_kind=_ARCHITECTURAL_KIND_BY_TAG.get(architectural_kind)
        if expected_kind is not None and observation.kind is not expected_kind: issues.append(SurveyValidationIssue("architectural_kind_mismatch",observation.id,f"L’observation déclare attributes.architectural_kind={architectural_kind!r} mais kind={observation.kind.value!r}. Elle doit utiliser kind={expected_kind.value!r}."))
        if observation.kind is ObservationKind.OPENING:
            physical_count=attributes.get("physical_object_count")
            if isinstance(physical_count,bool) or physical_count!=1: issues.append(SurveyValidationIssue("opening_not_single_physical_object",observation.id,"Chaque observation kind='opening' doit représenter exactement une ouverture physique et déclarer attributes.physical_object_count=1. Ne regroupez jamais plusieurs fenêtres ou portes sous un seul ID ; créez un ID stable par ouverture et dédupliquez seulement les occurrences multi-vues du même objet."))
            confirmed=bool(attributes.get("confirmed_by_user",False)); semantic_role=attributes.get("semantic_role") or attributes.get("semantic_type")
            if confirmed and (not isinstance(semantic_role,str) or not semantic_role.strip()): issues.append(SurveyValidationIssue("confirmed_opening_missing_semantic_role",observation.id,"User-confirmed opening requires a stable semantic_role; visual ambiguity may not erase its identity."))
            if observation.certainty in {Certainty.CERTAIN,Certainty.PLAUSIBLE} and target_ownership=="unproven": issues.append(SurveyValidationIssue("opening_target_ownership_unproven",observation.id,"Opening ownership by the target building is unproven; mark the observation unproven or context until new evidence exists."))
            for field in ("facade_horizontal_rank","facade_vertical_rank"):
                value=attributes.get(field)
                if value is not None and not _valid_positive_rank(value): issues.append(SurveyValidationIssue("invalid_opening_layout_rank",observation.id,f"{field} doit être un entier positif 1..N lorsqu’il est renseigné. Ces rangs sont qualitatifs et ne doivent pas contenir de mètres, pixels ou texte libre."))
        if observation.kind is ObservationKind.ROOF:
            roof_edge=attributes.get("roof_edge_type")
            if observation.facade is not None and observation.facade.value=="front":
                gable_end=attributes.get("facade_roof_relationship")=="gable_end"
                if gable_end and roof_edge=="eave_across_facade": issues.append(SurveyValidationIssue("gable_eave_terminology_conflict",observation.id,"A gable-end front facade cannot simultaneously have a horizontal eave across that facade; use rake/gable-edge terminology."))
            if len({item.photo_index for item in observation.evidence})>=2 and not _meaningful_roof_shape_hypothesis(attributes):
                issues.append(SurveyValidationIssue("multiview_roof_missing_shape_hypothesis",observation.id,"Une toiture recoupée dans plusieurs vues ne peut pas perdre toute hypothèse qualitative de forme. Conservez roof_type/facade_is_gable ou une relation de rive avec sa certitude d’attribut ; n’inventez aucune métrique."))
    issues.extend(_validate_refinement_semantics(survey)); return issues

def validate_survey_extension(base: ArchitecturalSurvey,candidate: ArchitecturalSurvey)->list[SurveyValidationIssue]:
    issues=[]
    if candidate.id!=base.id: issues.append(SurveyValidationIssue("survey_extension_id_changed",None,"Le Survey étendu doit conserver exactement le même id que le Survey validé de départ."))
    if candidate.canonical_frame!=base.canonical_frame: issues.append(SurveyValidationIssue("survey_extension_frame_changed",None,"Le repère canonique du Survey validé ne peut pas être modifié pendant une extension."))
    if candidate.known_measurements!=base.known_measurements: issues.append(SurveyValidationIssue("survey_extension_measurements_changed",None,"Les mesures connues du Survey validé doivent être conservées exactement pendant une extension."))
    if candidate.representation_policy!=base.representation_policy: issues.append(SurveyValidationIssue("survey_extension_policy_changed",None,"La politique de représentation du Survey validé ne peut pas être modifiée pendant une extension."))
    candidate_photos={p.photo_index:p for p in candidate.photos}; base_photo_indexes={p.photo_index for p in base.photos}
    for photo in base.photos:
        if photo.photo_index not in candidate_photos: issues.append(SurveyValidationIssue("survey_extension_photo_removed",None,f"La photo {photo.photo_index} du Survey validé a disparu du Survey étendu."))
        elif candidate_photos[photo.photo_index]!=photo: issues.append(SurveyValidationIssue("survey_extension_photo_changed",None,f"La description/orientation de la photo {photo.photo_index} a été modifiée. Une extension doit la conserver exactement."))
    base_max_photo=max(photo.photo_index for photo in base.photos)
    for photo in candidate.photos:
        if photo.photo_index not in base_photo_indexes and photo.photo_index<=base_max_photo: issues.append(SurveyValidationIssue("survey_extension_photo_index_reused",None,f"La nouvelle photo {photo.photo_index} réutilise un index ancien. Les nouvelles photos doivent commencer après {base_max_photo}."))
    candidate_observations={o.id:o for o in candidate.observations}
    for observation in base.observations:
        current=candidate_observations.get(observation.id)
        if current is None: issues.append(SurveyValidationIssue("survey_extension_observation_removed",observation.id,f"L’observation validée '{observation.id}' a disparu du Survey étendu."))
        elif current!=observation: issues.append(SurveyValidationIssue("survey_extension_observation_changed",observation.id,f"L’observation validée '{observation.id}' a été modifiée. Une extension doit conserver exactement les observations existantes et seulement en ajouter de nouvelles."))
    candidate_relations={r.id:r for r in candidate.relations}
    for relation in base.relations:
        current=candidate_relations.get(relation.id)
        if current is None: issues.append(SurveyValidationIssue("survey_extension_relation_removed",None,f"La relation validée '{relation.id}' a disparu du Survey étendu."))
        elif current!=relation: issues.append(SurveyValidationIssue("survey_extension_relation_changed",None,f"La relation validée '{relation.id}' a été modifiée. Une extension doit conserver exactement les relations existantes et seulement en ajouter de nouvelles."))
    issues.extend(validate_survey_semantics(candidate)); return issues