"""Cross-check an ArchitecturalScene against its validated ArchitecturalSurvey source."""
from __future__ import annotations

from collections import Counter
from enum import Enum
from math import dist
from pydantic import BaseModel

from brickhouse.building import Facade, OpeningType, RidgeDirection, RoofType
from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind, RelationKind

from .models import ArchitecturalScene, CONNECTIVITY_TOLERANCE_M


class SceneSurveySeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class SceneSurveyIssue(BaseModel):
    code: str
    severity: SceneSurveySeverity
    message: str
    object_id: str | None = None


def _semantic_opening_type(value: object) -> OpeningType | None:
    """Return only strong semantic mappings; ambiguous certain voids still must survive."""
    if value == "window":
        return OpeningType.WINDOW
    if value in {"door", "door_or_glazed_door", "glazed_door_or_large_glazed_opening"}:
        return OpeningType.DOOR
    if value == "garage_door":
        return OpeningType.GARAGE_DOOR
    return None


def _host_is_secondary(observation) -> bool:
    """Keep openings explicitly hosted by an annex out of main-wall count gates."""
    return bool(observation.attributes.get("host_object"))


def _opening_threshold(scene: ArchitecturalScene, opening_id: str) -> tuple[float, float, float] | None:
    opening = next((item for item in scene.openings if item.id == opening_id), None)
    if opening is None:
        return None
    volume = next((item for item in scene.volumes if item.id == opening.volume_id), None)
    if volume is None:
        return None
    center = opening.offset_horizontal + opening.width / 2
    x0, y0, z0 = volume.position.x, volume.position.y, volume.position.z
    x1 = x0 + volume.width.value
    y1 = y0 + volume.depth.value
    z = z0 + opening.offset_vertical
    if opening.facade is Facade.FRONT:
        return (x0 + center, y0, z)
    if opening.facade is Facade.RIGHT:
        return (x1, y0 + center, z)
    if opening.facade is Facade.REAR:
        return (x1 - center, y1, z)
    return (x0, y1 - center, z)


def _point_on_platform(point: tuple[float, float, float], platform) -> bool:
    x, y, z = point
    return (
        platform.position.x - CONNECTIVITY_TOLERANCE_M <= x <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
        and platform.position.y - CONNECTIVITY_TOLERANCE_M <= y <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
        and abs(z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
    )


def _stair_touches_platform(stair, platform) -> bool:
    return any(_point_on_platform((point.x, point.y, point.z), platform) for point in (stair.start, stair.end))


def _stair_touches_stair(first, second) -> bool:
    endpoints_a = [(first.start.x, first.start.y, first.start.z), (first.end.x, first.end.y, first.end.z)]
    endpoints_b = [(second.start.x, second.start.y, second.start.z), (second.end.x, second.end.y, second.end.z)]
    return any(dist(a, b) <= CONNECTIVITY_TOLERANCE_M for a in endpoints_a for b in endpoints_b)


def _platform_touches_platform(first, second) -> bool:
    if abs(first.position.z - second.position.z) > CONNECTIVITY_TOLERANCE_M:
        return False
    ax0, ax1 = first.position.x, first.position.x + first.width
    ay0, ay1 = first.position.y, first.position.y + first.depth
    bx0, bx1 = second.position.x, second.position.x + second.width
    by0, by1 = second.position.y, second.position.y + second.depth
    x_gap = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    y_gap = max(0.0, max(ay0, by0) - min(ay1, by1))
    return x_gap <= CONNECTIVITY_TOLERANCE_M and y_gap <= CONNECTIVITY_TOLERANCE_M


def _certain_connection_holds(scene: ArchitecturalScene, subject_id: str, object_id: str) -> bool | None:
    platforms = {item.id: item for item in scene.platforms}
    stairs = {item.id: item for item in scene.stairs}
    openings = {item.id: item for item in scene.openings}

    if subject_id in stairs and object_id in platforms:
        return _stair_touches_platform(stairs[subject_id], platforms[object_id])
    if subject_id in platforms and object_id in stairs:
        return _stair_touches_platform(stairs[object_id], platforms[subject_id])
    if subject_id in stairs and object_id in stairs:
        return _stair_touches_stair(stairs[subject_id], stairs[object_id])
    if subject_id in platforms and object_id in platforms:
        return _platform_touches_platform(platforms[subject_id], platforms[object_id])
    if subject_id in openings and object_id in platforms:
        threshold = _opening_threshold(scene, subject_id)
        return threshold is not None and _point_on_platform(threshold, platforms[object_id])
    if subject_id in platforms and object_id in openings:
        threshold = _opening_threshold(scene, object_id)
        return threshold is not None and _point_on_platform(threshold, platforms[subject_id])
    return None


def validate_scene_against_survey(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> list[SceneSurveyIssue]:
    """Reject semantic, inventory, relation or metric drift introduced during Survey -> Scene."""
    issues: list[SceneSurveyIssue] = []
    survey_openings = {item.id: item for item in survey.observations if item.kind is ObservationKind.OPENING}

    front_width = next((item for item in survey.known_measurements if item.kind == "front_width"), None)
    if front_width is not None:
        main_volume = scene.volumes[0] if scene.volumes else None
        if main_volume is None or abs(main_volume.width.value - front_width.value) > 1e-6:
            actual = main_volume.width.value if main_volume is not None else None
            issues.append(SceneSurveyIssue(code="front_width_measurement_drift", severity=SceneSurveySeverity.ERROR, object_id=main_volume.id if main_volume else None, message=f"La largeur avant mesurée dans le Survey vaut {front_width.value:g} m, mais la scène utilise {actual!r}."))
        elif main_volume.width.source.kind.value != "user_provided":
            issues.append(SceneSurveyIssue(code="front_width_provenance_drift", severity=SceneSurveySeverity.ERROR, object_id=main_volume.id, message="La largeur avant est une mesure utilisateur et doit conserver source.kind='user_provided' dans la scène."))

    for opening in scene.openings:
        observation = survey_openings.get(opening.id)
        if observation is None:
            issues.append(SceneSurveyIssue(code="scene_opening_not_in_survey", severity=SceneSurveySeverity.ERROR, object_id=opening.id, message=f"L’ouverture {opening.id!r} n’existe pas dans le relevé architectural validé."))
            continue
        if observation.certainty is Certainty.UNPROVEN:
            issues.append(SceneSurveyIssue(code="unproven_opening_promoted", severity=SceneSurveySeverity.ERROR, object_id=opening.id, message=f"L’ouverture {opening.id!r} était non prouvée dans le Survey et ne peut pas devenir une géométrie de scène."))
        if observation.facade is not None and opening.facade is not observation.facade:
            issues.append(SceneSurveyIssue(code="opening_facade_drift", severity=SceneSurveySeverity.ERROR, object_id=opening.id, message=f"L’ouverture {opening.id!r} a changé de façade entre le Survey et la scène."))
        expected = _semantic_opening_type(observation.attributes.get("semantic_type"))
        if expected is not None and opening.type is not expected:
            issues.append(SceneSurveyIssue(code="opening_type_drift", severity=SceneSurveySeverity.ERROR, object_id=opening.id, message=f"Le type de {opening.id!r} ne respecte pas l’identité sémantique du Survey."))

    scene_opening_ids = {item.id for item in scene.openings}
    for observation in survey_openings.values():
        if observation.certainty is Certainty.CERTAIN and observation.id not in scene_opening_ids:
            issues.append(SceneSurveyIssue(code="certain_opening_missing", severity=SceneSurveySeverity.ERROR, object_id=observation.id, message=f"L’ouverture certaine {observation.id!r} du Survey a disparu de la scène. Le nombre d’ouvertures doit être verrouillé avant leur type, position et dimensions."))

    main_survey_counts = Counter(
        observation.facade
        for observation in survey_openings.values()
        if observation.certainty is Certainty.CERTAIN and observation.facade is not None and not _host_is_secondary(observation)
    )
    main_volume_id = scene.volumes[0].id if scene.volumes else None
    main_scene_counts = Counter(opening.facade for opening in scene.openings if opening.volume_id == main_volume_id)
    documented_facades = {photo.facade for photo in survey.photos}
    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        if facade not in documented_facades:
            continue
        expected_count = main_survey_counts.get(facade, 0)
        actual_count = main_scene_counts.get(facade, 0)
        if actual_count != expected_count:
            issues.append(SceneSurveyIssue(code="facade_opening_count_drift", severity=SceneSurveySeverity.ERROR, message=f"La façade principale {facade.value} doit conserver exactement {expected_count} ouverture(s) certaine(s) du Survey, mais la scène en contient {actual_count}."))

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        if facade in documented_facades:
            continue
        if any(opening.facade is facade for opening in scene.openings):
            issues.append(SceneSurveyIssue(code="opening_on_undocumented_facade", severity=SceneSurveySeverity.ERROR, message=f"La scène ajoute une ouverture sur la façade {facade.value}, non documentée par ce Survey."))

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
            if opening_start < span.to_offset and opening_end > span.from_offset:
                issues.append(SceneSurveyIssue(code="opening_in_hidden_span", severity=SceneSurveySeverity.ERROR, object_id=opening.id, message=f"L’ouverture {opening.id!r} intersecte une zone {span.state.value} de la façade {opening.facade.value}; une zone cachée ne peut pas être complétée par supposition."))
                break

    certain_grade_facades = {item.facade for item in survey.observations if item.kind is ObservationKind.TERRAIN and item.certainty is Certainty.CERTAIN and item.facade is not None and item.attributes.get("slope_direction")}
    scene_grade_facades = {profile.facade for profile in (scene.terrain.profiles if scene.terrain else [])}
    for facade in certain_grade_facades - scene_grade_facades:
        issues.append(SceneSurveyIssue(code="certain_grade_missing", severity=SceneSurveySeverity.ERROR, message=f"La pente certaine du terrain sur la façade {facade.value} n’est pas conservée dans la scène."))

    front_gable = any(item.kind is ObservationKind.ROOF and item.certainty is Certainty.CERTAIN and item.facade is Facade.FRONT and item.attributes.get("front_is_gable") is True for item in survey.observations)
    if front_gable:
        gable_roofs = [roof for roof in scene.roofs if roof.type is RoofType.GABLE]
        if not gable_roofs:
            issues.append(SceneSurveyIssue(code="front_gable_lost", severity=SceneSurveySeverity.ERROR, message="Le Survey établit un pignon avant, mais la scène ne contient pas de toiture à deux pans."))
        elif any(roof.ridge_direction is not RidgeDirection.DEPTH for roof in gable_roofs):
            issues.append(SceneSurveyIssue(code="front_gable_ridge_mismatch", severity=SceneSurveySeverity.ERROR, message="Un pignon avant implique ici un faîtage avant→arrière (ridge_direction=depth)."))

    certain_chimneys = [item for item in survey.observations if item.kind is ObservationKind.CHIMNEY and item.certainty is Certainty.CERTAIN]
    if certain_chimneys and not scene.chimneys:
        issues.append(SceneSurveyIssue(code="certain_chimney_missing", severity=SceneSurveySeverity.ERROR, message="Une cheminée certaine du Survey a disparu de la scène."))

    scene_ids_by_kind = {
        ObservationKind.VOLUME: {item.id for item in scene.volumes},
        ObservationKind.PLATFORM: {item.id for item in scene.platforms},
        ObservationKind.STAIR: {item.id for item in scene.stairs},
    }
    missing_codes = {ObservationKind.VOLUME: "certain_volume_missing", ObservationKind.PLATFORM: "certain_platform_missing", ObservationKind.STAIR: "certain_stair_missing"}
    labels = {ObservationKind.VOLUME: "volume architectural", ObservationKind.PLATFORM: "plateforme/terrasse", ObservationKind.STAIR: "escalier"}
    for observation in survey.observations:
        if observation.certainty is not Certainty.CERTAIN or observation.kind not in scene_ids_by_kind:
            continue
        if observation.id not in scene_ids_by_kind[observation.kind]:
            issues.append(SceneSurveyIssue(code=missing_codes[observation.kind], severity=SceneSurveySeverity.ERROR, object_id=observation.id, message=f"Le {labels[observation.kind]} certain {observation.id!r} du Survey a disparu de la scène ou a changé d’id."))

    # Only explicit CERTAIN Survey connections become hard geometric constraints.
    # A missing relation is never inferred from architectural convention.
    for relation in survey.relations:
        if relation.kind is not RelationKind.CONNECTS_TO or relation.certainty is not Certainty.CERTAIN:
            continue
        holds = _certain_connection_holds(scene, relation.subject_id, relation.object_id)
        if holds is False:
            issues.append(SceneSurveyIssue(
                code="certain_connection_broken",
                severity=SceneSurveySeverity.ERROR,
                object_id=relation.subject_id,
                message=f"La relation certaine {relation.id!r} ({relation.subject_id} connects_to {relation.object_id}) est établie par le Survey mais n’est pas respectée géométriquement dans la Scene.",
            ))
        elif holds is None:
            issues.append(SceneSurveyIssue(
                code="certain_connection_not_yet_checkable",
                severity=SceneSurveySeverity.WARNING,
                object_id=relation.subject_id,
                message=f"La relation certaine {relation.id!r} est conservée comme fait du Survey, mais cette paire de types n’a pas encore de contrôle géométrique automatique.",
            ))

    return issues
