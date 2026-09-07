"""Conservative physical-support analysis for metric ArchitecturalScene geometry.

This module never synthesizes supports or hidden geometry. It distinguishes
proven support/contact from unresolved geometry and explicit contradictions so
later LEGO projection can block floating assemblies without rewriting Scene.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.survey import RelationKind

from .models import CONNECTIVITY_TOLERANCE_M, SceneRoofType
from .stair_contact import stair_endpoint_touches_run


SupportState = Literal["proven", "unresolved", "contradicted"]
SupportKind = Literal[
    "platform_host_contact",
    "platform_post_support",
    "stair_endpoint_support",
    "roof_host_support",
    "chimney_host_support",
    "explicit_support_relation",
]


class PhysicalSupportFact(BaseModel):
    kind: SupportKind
    object_id: str
    supporter_id: str | None = None
    endpoint: Literal["start", "end"] | None = None
    state: SupportState
    reason: str = Field(min_length=1)


class PhysicalSupportIssue(BaseModel):
    code: str
    severity: Literal["warning", "blocker"]
    object_id: str
    message: str = Field(min_length=1)


def _volume_dimensions(volume) -> tuple[float, float, float] | None:
    values = (volume.width.value, volume.depth.value, volume.height.value)
    if any(value is None for value in values):
        return None
    return values  # type: ignore[return-value]


def _intervals_overlap(a0: float, a1: float, b0: float, b1: float, *, tolerance: float = 0.0) -> bool:
    return min(a1, b1) >= max(a0, b0) - tolerance


def _platform_touches_volume(platform, volume) -> SupportState:
    dims = _volume_dimensions(volume)
    if dims is None:
        return "unresolved"
    width, depth, height = dims
    vx0, vx1 = volume.position.x, volume.position.x + width
    vy0, vy1 = volume.position.y, volume.position.y + depth
    vz0, vz1 = volume.position.z, volume.position.z + height
    px0, px1 = platform.position.x, platform.position.x + platform.width
    py0, py1 = platform.position.y, platform.position.y + platform.depth
    pz0, pz1 = platform.position.z - platform.thickness, platform.position.z

    x_overlap = _intervals_overlap(px0, px1, vx0, vx1, tolerance=CONNECTIVITY_TOLERANCE_M)
    y_overlap = _intervals_overlap(py0, py1, vy0, vy1, tolerance=CONNECTIVITY_TOLERANCE_M)
    z_overlap = _intervals_overlap(pz0, pz1, vz0, vz1, tolerance=CONNECTIVITY_TOLERANCE_M)
    x_boundary = min(abs(px0 - vx1), abs(px1 - vx0)) <= CONNECTIVITY_TOLERANCE_M
    y_boundary = min(abs(py0 - vy1), abs(py1 - vy0)) <= CONNECTIVITY_TOLERANCE_M
    if (x_boundary and y_overlap and z_overlap) or (y_boundary and x_overlap and z_overlap):
        return "proven"
    return "contradicted"


def _platform_supports_volume(platform, volume) -> SupportState:
    dims = _volume_dimensions(volume)
    if dims is None:
        return "unresolved"
    width, depth, _ = dims
    vx0, vx1 = volume.position.x, volume.position.x + width
    vy0, vy1 = volume.position.y, volume.position.y + depth
    px0, px1 = platform.position.x, platform.position.x + platform.width
    py0, py1 = platform.position.y, platform.position.y + platform.depth
    xy_overlap = _intervals_overlap(px0, px1, vx0, vx1) and _intervals_overlap(py0, py1, vy0, vy1)
    vertical_contact = abs(platform.position.z - volume.position.z) <= CONNECTIVITY_TOLERANCE_M
    return "proven" if xy_overlap and vertical_contact else "contradicted"


def _post_support_state(platform, post) -> SupportState:
    post_top = post.position.z + post.height
    vertical_contact = abs(post_top - (platform.position.z - platform.thickness)) <= CONNECTIVITY_TOLERANCE_M
    grounded = post.position.z <= CONNECTIVITY_TOLERANCE_M
    px0, px1 = platform.position.x, platform.position.x + platform.width
    py0, py1 = platform.position.y, platform.position.y + platform.depth
    sx0, sx1 = post.position.x, post.position.x + post.width
    sy0, sy1 = post.position.y, post.position.y + post.depth
    footprint_contact = _intervals_overlap(px0, px1, sx0, sx1) and _intervals_overlap(py0, py1, sy0, sy1)
    return "proven" if vertical_contact and grounded and footprint_contact else "contradicted"


def _point_on_platform(point, platform) -> bool:
    return (
        platform.position.x - CONNECTIVITY_TOLERANCE_M
        <= point.x
        <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
        and platform.position.y - CONNECTIVITY_TOLERANCE_M
        <= point.y
        <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
        and abs(point.z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
    )


def _stair_endpoint_state(scene, stair, endpoint_name: Literal["start", "end"]) -> tuple[SupportState, str | None]:
    point = getattr(stair, endpoint_name)
    if point.z <= CONNECTIVITY_TOLERANCE_M:
        return "proven", "ground"
    for platform in scene.platforms:
        if _point_on_platform(point, platform):
            return "proven", platform.id
    for other in scene.stairs:
        if other.id != stair.id and stair_endpoint_touches_run(point, other):
            return "proven", other.id
    return "unresolved", None


def _roof_host_state(roof, volume) -> SupportState:
    """A roof is supported by its explicit host only when the host envelope is metric."""
    return "proven" if _volume_dimensions(volume) is not None else "unresolved"


def _chimney_flat_roof_state(chimney, roof, volume) -> SupportState:
    """Validate only a flat roof plane; pitched planes need explicit constructible geometry."""
    dims = _volume_dimensions(volume)
    if dims is None:
        return "unresolved"
    if roof.type is not SceneRoofType.FLAT:
        return "unresolved"

    width, depth, height = dims
    vx0, vx1 = volume.position.x, volume.position.x + width
    vy0, vy1 = volume.position.y, volume.position.y + depth
    cx0, cx1 = chimney.position.x, chimney.position.x + chimney.width
    cy0, cy1 = chimney.position.y, chimney.position.y + chimney.depth
    footprint_overlap = (
        _intervals_overlap(cx0, cx1, vx0, vx1, tolerance=CONNECTIVITY_TOLERANCE_M)
        and _intervals_overlap(cy0, cy1, vy0, vy1, tolerance=CONNECTIVITY_TOLERANCE_M)
    )
    roof_z = volume.position.z + height
    chimney_bottom = chimney.position.z
    chimney_top = chimney.position.z + chimney.height
    crosses_roof_plane = (
        chimney_bottom <= roof_z + CONNECTIVITY_TOLERANCE_M
        and chimney_top >= roof_z - CONNECTIVITY_TOLERANCE_M
    )
    return "proven" if footprint_overlap and crosses_roof_plane else "contradicted"


def _chimney_support_state(scene, chimney) -> tuple[SupportState, str | None]:
    volumes = {item.id: item for item in scene.volumes}
    proven_roofs: list[str] = []
    unresolved_roofs: list[str] = []
    contradicted_roofs: list[str] = []
    for roof in sorted(scene.roofs, key=lambda item: item.id):
        volume = volumes.get(roof.volume_id)
        if volume is None:
            continue
        state = _chimney_flat_roof_state(chimney, roof, volume)
        if state == "proven":
            proven_roofs.append(roof.id)
        elif state == "unresolved":
            unresolved_roofs.append(roof.id)
        else:
            contradicted_roofs.append(roof.id)

    if len(proven_roofs) == 1:
        return "proven", proven_roofs[0]
    if len(proven_roofs) > 1:
        return "unresolved", None
    if unresolved_roofs:
        return "unresolved", None
    if contradicted_roofs:
        return "contradicted", contradicted_roofs[0] if len(contradicted_roofs) == 1 else None
    return "unresolved", None


def analyze_physical_support(scene) -> tuple[list[PhysicalSupportFact], list[PhysicalSupportIssue]]:
    """Return deterministic support facts and blockers without mutating ``scene``."""
    facts: list[PhysicalSupportFact] = []
    issues: list[PhysicalSupportIssue] = []
    volumes = {item.id: item for item in scene.volumes}
    platforms = {item.id: item for item in scene.platforms}
    roofs = {item.id: item for item in scene.roofs}
    chimneys = {item.id: item for item in scene.chimneys}

    default_host_id = scene.volumes[0].id if scene.volumes else None
    for platform in sorted(scene.platforms, key=lambda item: item.id):
        host_id = platform.host_volume_id or default_host_id
        if host_id is not None and host_id in volumes:
            state = _platform_touches_volume(platform, volumes[host_id])
            facts.append(PhysicalSupportFact(
                kind="platform_host_contact",
                object_id=platform.id,
                supporter_id=host_id,
                state=state,
                reason=(
                    "platform geometry touches its declared/default host volume"
                    if state == "proven"
                    else "host geometry is incomplete" if state == "unresolved"
                    else "platform geometry does not touch its declared/default host volume"
                ),
            ))
            if state == "contradicted" and platform.host_volume_id is not None:
                issues.append(PhysicalSupportIssue(
                    code="platform_host_contact_contradicted",
                    severity="blocker",
                    object_id=platform.id,
                    message=(
                        f"Platform {platform.id!r} declares host volume {host_id!r}, but metric geometry does not touch it. "
                        "No hidden bracket, cantilever, or offset is invented."
                    ),
                ))

        for post in sorted(platform.supports, key=lambda item: item.id):
            state = _post_support_state(platform, post)
            facts.append(PhysicalSupportFact(
                kind="platform_post_support",
                object_id=platform.id,
                supporter_id=post.id,
                state=state,
                reason=(
                    "post is grounded and reaches the platform underside"
                    if state == "proven"
                    else "post does not geometrically support the platform"
                ),
            ))
            if state == "contradicted":
                issues.append(PhysicalSupportIssue(
                    code="platform_support_post_not_supporting",
                    severity="blocker",
                    object_id=platform.id,
                    message=(
                        f"Support post {post.id!r} does not form a grounded geometric support chain to platform {platform.id!r}."
                    ),
                ))

    for stair in sorted(scene.stairs, key=lambda item: item.id):
        for endpoint_name in ("start", "end"):
            state, supporter_id = _stair_endpoint_state(scene, stair, endpoint_name)
            facts.append(PhysicalSupportFact(
                kind="stair_endpoint_support",
                object_id=stair.id,
                supporter_id=supporter_id,
                endpoint=endpoint_name,
                state=state,
                reason=(
                    f"stair endpoint contacts {supporter_id}"
                    if state == "proven"
                    else "no ground/platform/stair endpoint support is established"
                ),
            ))

    for roof in sorted(scene.roofs, key=lambda item: item.id):
        volume = volumes.get(roof.volume_id)
        state: SupportState = "contradicted" if volume is None else _roof_host_state(roof, volume)
        facts.append(PhysicalSupportFact(
            kind="roof_host_support",
            object_id=roof.id,
            supporter_id=roof.volume_id,
            state=state,
            reason=(
                "roof has an explicit metric host volume envelope"
                if state == "proven"
                else "roof host volume geometry is incomplete"
                if state == "unresolved"
                else "roof references no available host volume"
            ),
        ))
        if state == "contradicted":
            issues.append(PhysicalSupportIssue(
                code="roof_host_support_contradicted",
                severity="blocker",
                object_id=roof.id,
                message=f"Roof {roof.id!r} cannot be linked to its declared host volume {roof.volume_id!r}.",
            ))

    for chimney in sorted(scene.chimneys, key=lambda item: item.id):
        state, supporter_id = _chimney_support_state(scene, chimney)
        facts.append(PhysicalSupportFact(
            kind="chimney_host_support",
            object_id=chimney.id,
            supporter_id=supporter_id,
            state=state,
            reason=(
                "chimney footprint and vertical span cross one explicit flat roof plane"
                if state == "proven"
                else "chimney support is not uniquely provable from available roof geometry"
                if state == "unresolved"
                else "chimney geometry does not intersect the available flat roof plane"
            ),
        ))

    for relation in sorted(scene.relations, key=lambda item: item.id):
        if relation.kind is not RelationKind.SUPPORTS:
            continue
        if relation.geometry_status == "unresolved":
            facts.append(PhysicalSupportFact(
                kind="explicit_support_relation",
                object_id=relation.object_id,
                supporter_id=relation.subject_id,
                state="unresolved",
                reason="explicit support relation is topologically known but metric support is unresolved",
            ))
            continue

        state: SupportState = "unresolved"
        if relation.subject_id in platforms and relation.object_id in volumes:
            state = _platform_supports_volume(platforms[relation.subject_id], volumes[relation.object_id])
        elif relation.subject_id in roofs and relation.object_id in chimneys:
            roof = roofs[relation.subject_id]
            volume = volumes.get(roof.volume_id)
            state = "contradicted" if volume is None else _chimney_flat_roof_state(
                chimneys[relation.object_id], roof, volume
            )
        elif relation.subject_id in volumes and relation.object_id in chimneys:
            matching = [
                roof
                for roof in scene.roofs
                if roof.volume_id == relation.subject_id
            ]
            states = [
                _chimney_flat_roof_state(chimneys[relation.object_id], roof, volumes[relation.subject_id])
                for roof in matching
            ]
            if any(item == "proven" for item in states):
                state = "proven"
            elif any(item == "unresolved" for item in states):
                state = "unresolved"
            elif states:
                state = "contradicted"

        facts.append(PhysicalSupportFact(
            kind="explicit_support_relation",
            object_id=relation.object_id,
            supporter_id=relation.subject_id,
            state=state,
            reason=(
                "resolved support relation is reflected by metric geometry"
                if state == "proven"
                else "support geometry for this object pair is not representable"
                if state == "unresolved"
                else "resolved support relation contradicts metric geometry"
            ),
        ))
        if state == "contradicted":
            issues.append(PhysicalSupportIssue(
                code="resolved_support_relation_contradicted",
                severity="blocker",
                object_id=relation.object_id,
                message=(
                    f"Resolved support relation {relation.id!r} claims {relation.subject_id!r} supports "
                    f"{relation.object_id!r}, but metric geometry contradicts that claim."
                ),
            ))

    return facts, issues
