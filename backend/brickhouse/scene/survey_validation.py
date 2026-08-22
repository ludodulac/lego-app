"""Cross-check an ArchitecturalScene against its validated ArchitecturalSurvey source."""
from __future__ import annotations

from collections import Counter
from enum import Enum
from pydantic import BaseModel

from brickhouse.building import Facade, OpeningType, RidgeDirection, RoofType
from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import ArchitecturalScene


class SceneSurveySeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class SceneSurveyIssue(BaseModel):
    code: str
    severity: SceneSurveySeverity
    message: str
    object_id: str | None = None


def _semantic_opening_type(value: object) -> OpeningType | None:
    """Return only strong semantic mappings.

    Ambiguous but certain openings (glass blocks, indeterminate openings, etc.) are
    still required geometrically by the validator below; they are deliberately
    not forced into a window/door label here.
    """
    if value == "window":
        return OpeningType.WINDOW
    if value in {"door", "door_or_glazed_door", "glazed_door_or_large_glazed_opening"}:
        return OpeningType.DOOR
    if value == "garage_door":
        return OpeningType.GARAGE_DOOR
    return None


def validate_scene_against_survey(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> list[SceneSurveyIssue]:
    """Reject semantic or metric drift introduced during Survey -> Scene reconstruction."""
    issues: list[SceneSurveyIssue] = []
    survey_openings = {
        item.id: item
        for item in survey.observations
        if item.kind is ObservationKind.OPENING
    }

    front_width = next((item for item in survey.known_measurements if item.kind == "front_width"), None)
    if front_width is not None:
        main_volume = scene.volumes[0] if scene.volumes else None
        if main_volume is None or abs(main_volume.width.value - front_width.value) > 1e-6:
            actual = main_volume.width.value if main_volume is not None else None
            issues.append(SceneSurveyIssue(
                code="front_width_measurement_drift",
                severity=SceneSurveySeverity.ERROR,
                object_id=main_volume.id if main_volume is not None else None,
                message=f"La largeur avant mesurée dans le Survey vaut {front_width.value:g} m, mais la scène utilise {actual!r}.",
            ))
        elif main_volume.width.source.kind.value != "user_provided":
            issues.append(SceneSurveyIssue(
                code="front_width_provenance_drift",
                severity=SceneSurveySeverity.ERROR,
                object_id=main_volume.id,
                message="La largeur avant est une mesure utilisateur et doit conserver source.kind='user_provided' dans la scène.",
            ))

    for opening in scene.openings:
        observation = survey_openings.get(opening.id)
        if observation is None:
            issues.append(SceneSurveyIssue(
                code="scene_opening_not_in_survey",
                severity=SceneSurveySeverity.ERROR,
                object_id=opening.id,
                message=f"L’ouverture {opening.id!r} n’existe pas dans le relevé architectural validé.",
            ))
            continue
        if observation.certainty is Certainty.UNPROVEN:
            issues.append(SceneSurveyIssue(
                code="unproven_opening_promoted",
                severity=SceneSurveySeverity.ERROR,
                object_id=opening.id,
                message=f"L’ouverture {opening.id!r} était non prouvée dans le Survey et ne peut pas devenir une géométrie de scène.",
            ))
        if observation.facade is not None and opening.facade is not observation.facade:
            issues.append(SceneSurveyIssue(
                code="opening_facade_drift",
                severity=SceneSurveySeverity.ERROR,
                object_id=opening.id,
                message=f"L’ouverture {opening.id!r} a changé de façade entre le Survey et la scène.",
            ))
        expected = _semantic_opening_type(observation.attributes.get("semantic_type"))
        if expected is not None and opening.type is not expected:
            issues.append(SceneSurveyIssue(
                code="opening_type_drift",
                severity=SceneSurveySeverity.ERROR,
                object_id=opening.id,
                message=f"Le type de {opening.id!r} ne respecte pas l’identité sémantique du Survey.",
            ))

    # Hierarchy gate #1: a certain opening is first and foremost a physical void.
    # It may have an ambiguous semantic label, but it must not disappear from the
    # Scene merely because BuildingModel has a smaller type vocabulary.
    scene_opening_ids = {item.id for item in scene.openings}
    for observation in survey_openings.values():
        if observation.certainty is not Certainty.CERTAIN:
            continue
        if observation.id not in scene_opening_ids:
            issues.append(SceneSurveyIssue(
                code="certain_opening_missing",
                severity=SceneSurveySeverity.ERROR,
                object_id=observation.id,
                message=f"L’ouverture certaine {observation.id!r} du Survey a disparu de la scène. Le nombre d’ouvertures doit être verrouillé avant leur type, position et dimensions.",
            ))

    # Hierarchy gate #2: expose facade-level count drift explicitly. This makes
    # failures understandable and prevents downstream reconstruction from hiding
    # several missing openings behind individual warnings.
    survey_counts = Counter(
        observation.facade
        for observation in survey_openings.values()
        if observation.certainty is Certainty.CERTAIN and observation.facade is not None
    )
    scene_counts = Counter(opening.facade for opening in scene.openings)
    for facade, expected_count in survey_counts.items():
        actual_count = scene_counts.get(facade, 0)
        if actual_count != expected_count:
            issues.append(SceneSurveyIssue(
                code="facade_opening_count_drift",
                severity=SceneSurveySeverity.ERROR,
                message=f"La façade {facade.value} doit conserver {expected_count} ouverture(s) certaine(s) du Survey, mais la scène en contient {actual_count}.",
            ))

    photographed_facades = {photo.facade for photo in survey.photos}
    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        if facade in photographed_facades:
            continue
        if any(opening.facade is facade for opening in scene.openings):
            issues.append(SceneSurveyIssue(
                code="opening_on_undocumented_facade",
                severity=SceneSurveySeverity.ERROR,
                message=f"La scène ajoute une ouverture sur la façade {facade.value}, non documentée par ce Survey.",
            ))

    visibility_by_facade = {item.facade: item for item in scene.visibility}
    for opening in scene.openings:
        visibility = visibility_by_facade.get(opening.facade)
        if visibility is None:
            continue
        opening_start = opening.offset_horizontal
        opening_end = opening.offset_horizontal + opening.width
        for span in visibility.spans:
            if span.state.value == "visible":
                continue
            overlap = opening_start < span.to_offset and opening_end > span.from_offset
            if overlap:
                issues.append(SceneSurveyIssue(
                    code="opening_in_hidden_span",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=opening.id,
                    message=f"L’ouverture {opening.id!r} intersecte une zone {span.state.value} de la façade {opening.facade.value}; une zone cachée ne peut pas être complétée par supposition.",
                ))
                break

    certain_grade_facades = {
        item.facade
        for item in survey.observations
        if item.kind is ObservationKind.TERRAIN
        and item.certainty is Certainty.CERTAIN
        and item.facade is not None
        and item.attributes.get("slope_direction")
    }
    scene_grade_facades = {profile.facade for profile in (scene.terrain.profiles if scene.terrain else [])}
    for facade in certain_grade_facades - scene_grade_facades:
        issues.append(SceneSurveyIssue(
            code="certain_grade_missing",
            severity=SceneSurveySeverity.ERROR,
            message=f"La pente certaine du terrain sur la façade {facade.value} n’est pas conservée dans la scène.",
        ))

    front_gable = any(
        item.kind is ObservationKind.ROOF
        and item.certainty is Certainty.CERTAIN
        and item.facade is Facade.FRONT
        and item.attributes.get("front_is_gable") is True
        for item in survey.observations
    )
    if front_gable:
        gable_roofs = [roof for roof in scene.roofs if roof.type is RoofType.GABLE]
        if not gable_roofs:
            issues.append(SceneSurveyIssue(
                code="front_gable_lost",
                severity=SceneSurveySeverity.ERROR,
                message="Le Survey établit un pignon avant, mais la scène ne contient pas de toiture à deux pans.",
            ))
        elif any(roof.ridge_direction is not RidgeDirection.DEPTH for roof in gable_roofs):
            issues.append(SceneSurveyIssue(
                code="front_gable_ridge_mismatch",
                severity=SceneSurveySeverity.ERROR,
                message="Un pignon avant implique ici un faîtage avant→arrière (ridge_direction=depth).",
            ))

    certain_chimneys = [
        item for item in survey.observations
        if item.kind is ObservationKind.CHIMNEY and item.certainty is Certainty.CERTAIN
    ]
    if certain_chimneys and not scene.chimneys:
        issues.append(SceneSurveyIssue(
            code="certain_chimney_missing",
            severity=SceneSurveySeverity.ERROR,
            message="Une cheminée certaine du Survey a disparu de la scène.",
        ))

    scene_ids_by_kind = {
        ObservationKind.VOLUME: {item.id for item in scene.volumes},
        ObservationKind.PLATFORM: {item.id for item in scene.platforms},
        ObservationKind.STAIR: {item.id for item in scene.stairs},
    }
    missing_codes = {
        ObservationKind.VOLUME: "certain_volume_missing",
        ObservationKind.PLATFORM: "certain_platform_missing",
        ObservationKind.STAIR: "certain_stair_missing",
    }
    labels = {
        ObservationKind.VOLUME: "volume architectural",
        ObservationKind.PLATFORM: "plateforme/terrasse",
        ObservationKind.STAIR: "escalier",
    }
    for observation in survey.observations:
        if observation.certainty is not Certainty.CERTAIN or observation.kind not in scene_ids_by_kind:
            continue
        if observation.id not in scene_ids_by_kind[observation.kind]:
            issues.append(SceneSurveyIssue(
                code=missing_codes[observation.kind],
                severity=SceneSurveySeverity.ERROR,
                object_id=observation.id,
                message=f"Le {labels[observation.kind]} certain {observation.id!r} du Survey a disparu de la scène ou a changé d’id.",
            ))

    return issues