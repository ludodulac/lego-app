"""Validate explicit platform access against connected stair geometry.

ArchitecturalScene remains authoritative: this module never invents an opening in a
railing or parapet merely because a stair happens to touch a platform. Instead it
rejects the contradictory combination so the source Scene can be corrected or
completed with an evidence-backed access span.
"""
from __future__ import annotations

from brickhouse.scene.models import (
    ArchitecturalScene,
    CONNECTIVITY_TOLERANCE_M,
    EdgeTreatment,
)

_GUARDED = {EdgeTreatment.OPEN_RAILING, EdgeTreatment.SOLID_PARAPET}


def _single_boundary_edge(point, platform):
    if abs(point.z - platform.position.z) > CONNECTIVITY_TOLERANCE_M:
        return None

    x0 = platform.position.x
    x1 = x0 + platform.width
    y0 = platform.position.y
    y1 = y0 + platform.depth
    if not (
        x0 - CONNECTIVITY_TOLERANCE_M <= point.x <= x1 + CONNECTIVITY_TOLERANCE_M
        and y0 - CONNECTIVITY_TOLERANCE_M <= point.y <= y1 + CONNECTIVITY_TOLERANCE_M
    ):
        return None

    candidates = []
    if abs(point.x - x0) <= CONNECTIVITY_TOLERANCE_M:
        candidates.append(("x_min", point.y - y0, platform.depth))
    if abs(point.x - x1) <= CONNECTIVITY_TOLERANCE_M:
        candidates.append(("x_max", point.y - y0, platform.depth))
    if abs(point.y - y0) <= CONNECTIVITY_TOLERANCE_M:
        candidates.append(("y_min", point.x - x0, platform.width))
    if abs(point.y - y1) <= CONNECTIVITY_TOLERANCE_M:
        candidates.append(("y_max", point.x - x0, platform.width))

    # Corner contacts are ambiguous without richer topology. Do not fabricate
    # which edge owns the connection.
    return candidates[0] if len(candidates) == 1 else None


def _stair_is_normal_to_edge(stair, edge_name: str) -> bool:
    dx = abs(stair.end.x - stair.start.x)
    dy = abs(stair.end.y - stair.start.y)
    return dx >= dy if edge_name.startswith("x_") else dy >= dx


def _span_covers_stair(edge, center_offset: float, stair_width: float, edge_length: float) -> bool:
    required_from = center_offset - stair_width / 2
    required_to = center_offset + stair_width / 2
    if required_from < -CONNECTIVITY_TOLERANCE_M or required_to > edge_length + CONNECTIVITY_TOLERANCE_M:
        return False
    return any(
        span.from_offset <= required_from + CONNECTIVITY_TOLERANCE_M
        and span.to_offset >= required_to - CONNECTIVITY_TOLERANCE_M
        for span in edge.access_spans
    )


def validate_scene_stair_platform_access(scene: ArchitecturalScene) -> None:
    """Reject guarded platform/stair junctions without an explicit full-width gap."""
    for platform in scene.platforms:
        if platform.edges is None:
            continue
        for stair in scene.stairs:
            for endpoint_name, point in (("start", stair.start), ("end", stair.end)):
                boundary = _single_boundary_edge(point, platform)
                if boundary is None:
                    continue
                edge_name, center_offset, edge_length = boundary
                if not _stair_is_normal_to_edge(stair, edge_name):
                    continue
                edge = getattr(platform.edges, edge_name)
                if edge.treatment not in _GUARDED:
                    continue
                if _span_covers_stair(edge, center_offset, stair.width, edge_length):
                    continue
                raise ValueError(
                    f"stair {stair.id!r} {endpoint_name} meets guarded platform "
                    f"{platform.id!r} edge {edge_name} without an access span covering "
                    "the stair width"
                )
