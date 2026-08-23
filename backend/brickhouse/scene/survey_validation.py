"""Cross-check an ArchitecturalScene against its validated ArchitecturalSurvey source."""

from __future__ import annotations

from collections import Counter
from enum import Enum
from math import dist

from pydantic import BaseModel

from brickhouse.building import Facade, OpeningType, RidgeDirection
from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind, RelationKind

from .models import ArchitecturalScene, CONNECTIVITY_TOLERANCE_M, EdgeTreatment, SceneRoofType


class SceneSurveySeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class SceneSurveyIssue(BaseModel):
    code: str
    severity: SceneSurveySeverity
    message: str
    object_id: str | None = None


def _semantic_opening_type(value):
    if value == "window":
        return OpeningType.WINDOW
    if value in {"door", "door_or_glazed_door", "glazed_door_or_large_glazed_opening"}:
        return OpeningType.DOOR
    if value == "garage_door":
        return OpeningType.GARAGE_DOOR
    return None


def _host_is_secondary(observation):
    return bool(observation.attributes.get("host_object"))


def _opening_threshold(scene, opening_id):
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
        return x0 + center, y0, z
    if opening.facade is Facade.RIGHT:
        return x1, y0 + center, z
    if opening.facade is Facade.REAR:
        return x1 - center, y1, z
    return x0, y1 - center, z


def _point_on_platform(point, platform):
    x, y, z = point
    return (
        platform.position.x - CONNECTIVITY_TOLERANCE_M <= x <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
        and platform.position.y - CONNECTIVITY_TOLERANCE_M <= y <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
        and abs(z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
    )


def _stair_touches_platform(stair, platform):
    return any(_point_on_platform((point.x, point.y, point.z), platform) for point in (stair.start, stair.end))


def _stair_touches_stair(first, second):
    first_points = [(first.start.x, first.start.y, first.start.z), (first.end.x, first.end.y, first.end.z)]
    second_points = [(second.start.x, second.start.y, second.start.z), (second.end.x, second.end.y, second.end.z)]
    return any(dist(a, b) <= CONNECTIVITY_TOLERANCE_M for a in first_points for b in second_points)


def _platform_touches_platform(first, second):
    if abs(first.position.z - second.position.z) > CONNECTIVITY_TOLERANCE_M:
        return False
    ax0, ax1 = first.position.x, first.position.x + first.width
    ay0, ay1 = first.position.y, first.position.y + first.depth
    bx0, bx1 = second.position.x, second.position.x + second.width
    by0, by1 = second.position.y, second.position.y + second.depth
    x_gap = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    y_gap = max(0.0, max(ay0, by0) - min(ay1, by1))
    return x_gap <= CONNECTIVITY_TOLERANCE_M and y_gap <= CONNECTIVITY_TOLERANCE_M


def _edge_access_interval(edge, offset):
    if edge.treatment in {EdgeTreatment.NONE, EdgeTreatment.ACCESS_OPENING, EdgeTreatment.UNKNOWN}:
        return -float("inf"), float("inf")
    if edge.treatment is EdgeTreatment.WALL_ATTACHED:
        return None
    for span in edge.access_spans:
        if span.from_offset - CONNECTIVITY_TOLERANCE_M <= offset <= span.to_offset + CONNECTIVITY_TOLERANCE_M:
            return span.from_offset, span.to_offset
    return None


def _interval_contains(container, required):
    if container is None:
        return False
    return (
        required[0] >= container[0] - CONNECTIVITY_TOLERANCE_M
        and required[1] <= container[1] + CONNECTIVITY_TOLERANCE_M
    )


def _edge_allows_interval(edge, required):
    if edge.treatment in {EdgeTreatment.NONE, EdgeTreatment.ACCESS_OPENING, EdgeTreatment.UNKNOWN}:
        return True
    if edge.treatment is EdgeTreatment.WALL_ATTACHED:
        return False
    return any(_interval_contains((span.from_offset, span.to_offset), required) for span in edge.access_spans)


def _stair_cross_interval(stair, edge_name, endpoint, platform):
    half = stair.width / 2
    x0, y0 = platform.position.x, platform.position.y
    dx = abs(stair.end.x - stair.start.x)
    dy = abs(stair.end.y - stair.start.y)
    if edge_name in {"y_min", "y_max"}:
        center = endpoint.x - x0
        if dy >= dx:
            return center - half, center + half
        return center - CONNECTIVITY_TOLERANCE_M, center + CONNECTIVITY_TOLERANCE_M
    center = endpoint.y - y0
    if dx >= dy:
        return center - half, center + half
    return center - CONNECTIVITY_TOLERANCE_M, center + CONNECTIVITY_TOLERANCE_M


def _stair_platform_access_holds(stair, platform):
    if platform.edges is None:
        return True
    x0, x1 = platform.position.x, platform.position.x + platform.width
    y0, y1 = platform.position.y, platform.position.y + platform.depth
    checked = False
    for point in (stair.start, stair.end):
        if not _point_on_platform((point.x, point.y, point.z), platform):
            continue
        edges = []
        if abs(point.x - x0) <= CONNECTIVITY_TOLERANCE_M:
            edges.append(("x_min", platform.edges.x_min, point.y - y0))
        if abs(point.x - x1) <= CONNECTIVITY_TOLERANCE_M:
            edges.append(("x_max", platform.edges.x_max, point.y - y0))
        if abs(point.y - y0) <= CONNECTIVITY_TOLERANCE_M:
            edges.append(("y_min", platform.edges.y_min, point.x - x0))
        if abs(point.y - y1) <= CONNECTIVITY_TOLERANCE_M:
            edges.append(("y_max", platform.edges.y_max, point.x - x0))
        if not edges:
            return True
        checked = True
        for name, edge, offset in edges:
            required = _stair_cross_interval(stair, name, point, platform)
            if _interval_contains(_edge_access_interval(edge, offset), required):
                return True
    return not checked


def _platform_platform_access_holds(first, second):
    """Require protected shared edges to expose the whole real overlap between two connected platforms."""
    if first.edges is None and second.edges is None:
        return True

    ax0, ax1 = first.position.x, first.position.x + first.width
    ay0, ay1 = first.position.y, first.position.y + first.depth
    bx0, bx1 = second.position.x, second.position.x + second.width
    by0, by1 = second.position.y, second.position.y + second.depth
    candidates = []

    y0, y1 = max(ay0, by0), min(ay1, by1)
    if y1 >= y0 - CONNECTIVITY_TOLERANCE_M:
        if abs(ax1 - bx0) <= CONNECTIVITY_TOLERANCE_M:
            candidates.append(
                (
                    (first.edges.x_max if first.edges else None, (y0 - ay0, y1 - ay0)),
                    (second.edges.x_min if second.edges else None, (y0 - by0, y1 - by0)),
                )
            )
        if abs(bx1 - ax0) <= CONNECTIVITY_TOLERANCE_M:
            candidates.append(
                (
                    (first.edges.x_min if first.edges else None, (y0 - ay0, y1 - ay0)),
                    (second.edges.x_max if second.edges else None, (y0 - by0, y1 - by0)),
                )
            )

    x0, x1 = max(ax0, bx0), min(ax1, bx1)
    if x1 >= x0 - CONNECTIVITY_TOLERANCE_M:
        if abs(ay1 - by0) <= CONNECTIVITY_TOLERANCE_M:
            candidates.append(
                (
                    (first.edges.y_max if first.edges else None, (x0 - ax0, x1 - ax0)),
                    (second.edges.y_min if second.edges else None, (x0 - bx0, x1 - bx0)),
                )
            )
        if abs(by1 - ay0) <= CONNECTIVITY_TOLERANCE_M:
            candidates.append(
                (
                    (first.edges.y_min if first.edges else None, (x0 - ax0, x1 - ax0)),
                    (second.edges.y_max if second.edges else None, (x0 - bx0, x1 - bx0)),
                )
            )

    if not candidates:
        return True
    for pair in candidates:
        if all(edge is None or _edge_allows_interval(edge, required) for edge, required in pair):
            return True
    return False


def _certain_connection_holds(scene, subject_id, object_id):
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


def _local_grade_elevation(scene, opening):
    if scene.terrain is None:
        return None
    profile = next((item for item in scene.terrain.profiles if item.facade is opening.facade), None)
    if profile is None:
        return None
    volume = next((item for item in scene.volumes if item.id == opening.volume_id), None)
    if volume is None:
        return None
    span = volume.width.value if opening.facade in {Facade.FRONT, Facade.REAR} else volume.depth.value
    if span <= 0:
        return None
    center = min(max((opening.offset_horizontal + opening.width / 2) / span, 0.0), 1.0)
    return profile.start_elevation + (profile.end_elevation - profile.start_elevation) * center


def _certain_gable_facades(survey: ArchitecturalSurvey) -> set[Facade]:
    """Return facades proven to be gable walls without privileging the canonical front."""
    result: set[Facade] = set()
    for observation in survey.observations:
        if observation.kind is not ObservationKind.ROOF or observation.certainty is not Certainty.CERTAIN:
            continue
        if observation.facade is None:
            continue
        if observation.attributes.get("facade_is_gable") is True:
            result.add(observation.facade)
            continue
        # Backwards compatibility with surveys emitted before the generic field existed.
        if observation.facade is Facade.FRONT and observation.attributes.get("front_is_gable") is True:
            result.add(observation.facade)
    return result


def _gable_ridge_direction(facade: Facade) -> RidgeDirection:
    if facade in {Facade.FRONT, Facade.REAR}:
        return RidgeDirection.DEPTH
    return RidgeDirection.WIDTH


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    issues: list[SceneSurveyIssue] = []
    survey_openings = {item.id: item for item in survey.observations if item.kind is ObservationKind.OPENING}

    front_width = next((item for item in survey.known_measurements if item.kind == "front_width"), None)
    if front_width is not None:
        main = scene.volumes[0] if scene.volumes else None
        if main is None or abs(main.width.value - front_width.value) > 1e-6:
            issues.append(
                SceneSurveyIssue(
                    code="front_width_measurement_drift",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=main.id if main else None,
                    message=f"La largeur avant mesurée dans le Survey vaut {front_width.value:g} m, mais la scène utilise {main.width.value if main else None!r}.",
                )
            )
        elif main.width.source.kind.value != "user_provided":
            issues.append(
                SceneSurveyIssue(
                    code="front_width_provenance_drift",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=main.id,
                    message="La largeur avant utilisateur doit conserver source.kind='user_provided'.",
                )
            )

    for opening in scene.openings:
        observation = survey_openings.get(opening.id)
        if observation is None:
            issues.append(
                SceneSurveyIssue(
                    code="scene_opening_not_in_survey",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=opening.id,
                    message=f"L’ouverture {opening.id!r} n’existe pas dans le Survey validé.",
                )
            )
            continue
        if observation.certainty is Certainty.UNPROVEN:
            issues.append(
                SceneSurveyIssue(
                    code="unproven_opening_promoted",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=opening.id,
                    message=f"L’ouverture {opening.id!r} était non prouvée.",
                )
            )
        if observation.facade is not None and opening.facade is not observation.facade:
            issues.append(
                SceneSurveyIssue(
                    code="opening_facade_drift",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=opening.id,
                    message=f"L’ouverture {opening.id!r} a changé de façade.",
                )
            )
        expected = _semantic_opening_type(observation.attributes.get("semantic_type"))
        if expected is not None and opening.type is not expected:
            issues.append(
                SceneSurveyIssue(
                    code="opening_type_drift",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=opening.id,
                    message=f"Le type de {opening.id!r} ne respecte pas le Survey.",
                )
            )
        if opening.local_grade_clearance is not None:
            grade = _local_grade_elevation(scene, opening)
            volume = next((item for item in scene.volumes if item.id == opening.volume_id), None)
            if grade is None or volume is None:
                issues.append(
                    SceneSurveyIssue(
                        code="local_grade_clearance_uncheckable",
                        severity=SceneSurveySeverity.WARNING,
                        object_id=opening.id,
                        message=f"L’ouverture {opening.id!r} définit une garde au sol locale, mais aucun profil de terrain correspondant ne permet de la vérifier.",
                    )
                )
            else:
                actual = volume.position.z + opening.offset_vertical - grade
                if abs(actual - opening.local_grade_clearance) > 0.20:
                    issues.append(
                        SceneSurveyIssue(
                            code="local_grade_clearance_mismatch",
                            severity=SceneSurveySeverity.ERROR,
                            object_id=opening.id,
                            message=f"L’ouverture {opening.id!r} annonce une garde au sol locale de {opening.local_grade_clearance:g} m, mais sa géométrie et la pente donnent environ {actual:.2f} m.",
                        )
                    )

    scene_ids = {item.id for item in scene.openings}
    for observation in survey_openings.values():
        if observation.certainty is Certainty.CERTAIN and observation.id not in scene_ids:
            issues.append(
                SceneSurveyIssue(
                    code="certain_opening_missing",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=observation.id,
                    message=f"L’ouverture certaine {observation.id!r} a disparu de la Scene.",
                )
            )

    survey_counts = Counter(
        observation.facade
        for observation in survey_openings.values()
        if observation.certainty is Certainty.CERTAIN
        and observation.facade is not None
        and not _host_is_secondary(observation)
    )
    main_id = scene.volumes[0].id if scene.volumes else None
    scene_counts = Counter(opening.facade for opening in scene.openings if opening.volume_id == main_id)
    documented = {photo.facade for photo in survey.photos}
    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        if facade in documented and scene_counts.get(facade, 0) != survey_counts.get(facade, 0):
            issues.append(
                SceneSurveyIssue(
                    code="facade_opening_count_drift",
                    severity=SceneSurveySeverity.ERROR,
                    message=f"La façade {facade.value} doit conserver exactement {survey_counts.get(facade, 0)} ouverture(s), la Scene en contient {scene_counts.get(facade, 0)}.",
                )
            )
        elif facade not in documented and any(opening.facade is facade for opening in scene.openings):
            issues.append(
                SceneSurveyIssue(
                    code="opening_on_undocumented_facade",
                    severity=SceneSurveySeverity.ERROR,
                    message=f"La Scene ajoute une ouverture sur la façade non documentée {facade.value}.",
                )
            )

    visibility = {item.facade: item for item in scene.visibility}
    for opening in scene.openings:
        entry = visibility.get(opening.facade)
        if not entry:
            continue
        for span in entry.spans:
            if (
                span.state.value != "visible"
                and opening.offset_horizontal < span.to_offset
                and opening.offset_horizontal + opening.width > span.from_offset
            ):
                issues.append(
                    SceneSurveyIssue(
                        code="opening_in_hidden_span",
                        severity=SceneSurveySeverity.ERROR,
                        object_id=opening.id,
                        message=f"L’ouverture {opening.id!r} intersecte une zone {span.state.value}.",
                    )
                )
                break

    certain_grade = {
        observation.facade
        for observation in survey.observations
        if observation.kind is ObservationKind.TERRAIN
        and observation.certainty is Certainty.CERTAIN
        and observation.facade is not None
        and observation.attributes.get("slope_direction")
    }
    scene_grade = {profile.facade for profile in (scene.terrain.profiles if scene.terrain else [])}
    for facade in certain_grade - scene_grade:
        issues.append(
            SceneSurveyIssue(
                code="certain_grade_missing",
                severity=SceneSurveySeverity.ERROR,
                message=f"La pente certaine sur {facade.value} a disparu.",
            )
        )

    gable_facades = _certain_gable_facades(survey)
    if gable_facades:
        roofs = [roof for roof in scene.roofs if roof.type is SceneRoofType.GABLE]
        if not roofs:
            issues.append(
                SceneSurveyIssue(
                    code="certain_gable_lost",
                    severity=SceneSurveySeverity.ERROR,
                    message="Un ou plusieurs murs pignons certains ont disparu de la Scene.",
                )
            )
        else:
            expected_directions = {_gable_ridge_direction(facade) for facade in gable_facades}
            if len(expected_directions) > 1:
                issues.append(
                    SceneSurveyIssue(
                        code="conflicting_gable_facades",
                        severity=SceneSurveySeverity.ERROR,
                        message="Le Survey marque comme pignons certains des façades perpendiculaires incompatibles avec un unique toit à deux pans.",
                    )
                )
            else:
                expected_direction = next(iter(expected_directions))
                if any(roof.ridge_direction is not expected_direction for roof in roofs):
                    facades = ", ".join(sorted(facade.value for facade in gable_facades))
                    issues.append(
                        SceneSurveyIssue(
                            code="gable_ridge_mismatch",
                            severity=SceneSurveySeverity.ERROR,
                            message=f"Les murs pignons certains ({facades}) imposent ridge_direction={expected_direction.value}.",
                        )
                    )

    if any(
        observation.kind is ObservationKind.CHIMNEY and observation.certainty is Certainty.CERTAIN
        for observation in survey.observations
    ) and not scene.chimneys:
        issues.append(
            SceneSurveyIssue(
                code="certain_chimney_missing",
                severity=SceneSurveySeverity.ERROR,
                message="Une cheminée certaine a disparu.",
            )
        )

    ids_by_kind = {
        ObservationKind.VOLUME: {item.id for item in scene.volumes},
        ObservationKind.PLATFORM: {item.id for item in scene.platforms},
        ObservationKind.STAIR: {item.id for item in scene.stairs},
    }
    codes = {
        ObservationKind.VOLUME: "certain_volume_missing",
        ObservationKind.PLATFORM: "certain_platform_missing",
        ObservationKind.STAIR: "certain_stair_missing",
    }
    for observation in survey.observations:
        if (
            observation.certainty is Certainty.CERTAIN
            and observation.kind in ids_by_kind
            and observation.id not in ids_by_kind[observation.kind]
        ):
            issues.append(
                SceneSurveyIssue(
                    code=codes[observation.kind],
                    severity=SceneSurveySeverity.ERROR,
                    object_id=observation.id,
                    message=f"L’élément architectural certain {observation.id!r} a disparu ou changé d’id.",
                )
            )

    platforms = {item.id: item for item in scene.platforms}
    stairs = {item.id: item for item in scene.stairs}
    for relation in survey.relations:
        if relation.kind is not RelationKind.CONNECTS_TO or relation.certainty is not Certainty.CERTAIN:
            continue
        holds = _certain_connection_holds(scene, relation.subject_id, relation.object_id)
        if holds is False:
            issues.append(
                SceneSurveyIssue(
                    code="certain_connection_broken",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=relation.subject_id,
                    message=f"La relation certaine {relation.id!r} n’est pas respectée géométriquement.",
                )
            )
            continue
        if holds is None:
            issues.append(
                SceneSurveyIssue(
                    code="certain_connection_not_yet_checkable",
                    severity=SceneSurveySeverity.WARNING,
                    object_id=relation.subject_id,
                    message=f"La relation certaine {relation.id!r} n’a pas encore de contrôle géométrique automatique.",
                )
            )
            continue

        stair = None
        platform = None
        if relation.subject_id in stairs and relation.object_id in platforms:
            stair, platform = stairs[relation.subject_id], platforms[relation.object_id]
        elif relation.object_id in stairs and relation.subject_id in platforms:
            stair, platform = stairs[relation.object_id], platforms[relation.subject_id]
        if stair is not None and not _stair_platform_access_holds(stair, platform):
            issues.append(
                SceneSurveyIssue(
                    code="certain_connection_blocked_by_platform_edge",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=stair.id,
                    message=f"La relation certaine {relation.id!r} ne dispose pas d’un passage assez large pour toute la volée. Élargis/corrige access_spans ou la géométrie de l’escalier.",
                )
            )

        if relation.subject_id in platforms and relation.object_id in platforms:
            first, second = platforms[relation.subject_id], platforms[relation.object_id]
            if not _platform_platform_access_holds(first, second):
                issues.append(
                    SceneSurveyIssue(
                        code="certain_platform_transition_blocked",
                        severity=SceneSurveySeverity.ERROR,
                        object_id=first.id,
                        message=f"La relation certaine {relation.id!r} relie deux plateformes mais leur bord commun est bloqué par un garde-corps/muret continu ou un passage trop étroit.",
                    )
                )

    return issues
