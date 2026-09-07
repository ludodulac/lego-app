"""Deterministic spatial facts derived from ArchitecturalScene geometry.

This module is an internal understanding/readiness layer.  It does not add new
Survey relation kinds and it does not mutate or serialize new claims into the
ArchitecturalScene contract.  Instead it derives queryable geometric facts from
complete object envelopes in the canonical Scene frame (x left->right, y
front->rear, z bottom->top).

BH-164 deliberately starts with SceneVolume and Platform.  Missing volume metrics
produce explicit unknown geometry rather than guessed extents.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .models import CONNECTIVITY_TOLERANCE_M, EPSILON, Platform, SceneVolume


SpatialObjectKind = Literal["volume", "platform"]


class SceneObjectEnvelope(BaseModel):
    object_id: str
    object_kind: SpatialObjectKind
    geometry_known: bool
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None
    z_min: float | None = None
    z_max: float | None = None


class SpatialPairFacts(BaseModel):
    """Directional facts from ``subject_id`` toward ``object_id``."""

    subject_id: str
    object_id: str
    geometry_known: bool

    x_gap: float | None = Field(default=None, ge=0)
    y_gap: float | None = Field(default=None, ge=0)
    z_gap: float | None = Field(default=None, ge=0)
    x_overlap: float | None = Field(default=None, ge=0)
    y_overlap: float | None = Field(default=None, ge=0)
    z_overlap: float | None = Field(default=None, ge=0)

    left_of: bool | None = None
    right_of: bool | None = None
    front_of: bool | None = None
    behind: bool | None = None
    above: bool | None = None
    below: bool | None = None

    overlaps_xy: bool | None = None
    overlaps_3d: bool | None = None
    adjacent_face: bool | None = None
    contains_object: bool | None = None
    contained_by_object: bool | None = None


class SpatialRelationReport(BaseModel):
    scene_id: str
    envelopes: list[SceneObjectEnvelope]
    pairs: list[SpatialPairFacts]

    def relation(self, subject_id: str, object_id: str) -> SpatialPairFacts | None:
        return next(
            (
                pair
                for pair in self.pairs
                if pair.subject_id == subject_id and pair.object_id == object_id
            ),
            None,
        )


def _volume_envelope(volume: SceneVolume) -> SceneObjectEnvelope:
    values = (volume.width.value, volume.depth.value, volume.height.value)
    if any(value is None for value in values):
        return SceneObjectEnvelope(
            object_id=volume.id,
            object_kind="volume",
            geometry_known=False,
        )
    width, depth, height = values
    assert width is not None and depth is not None and height is not None
    return SceneObjectEnvelope(
        object_id=volume.id,
        object_kind="volume",
        geometry_known=True,
        x_min=volume.position.x,
        x_max=volume.position.x + width,
        y_min=volume.position.y,
        y_max=volume.position.y + depth,
        z_min=volume.position.z,
        z_max=volume.position.z + height,
    )


def _platform_envelope(platform: Platform) -> SceneObjectEnvelope:
    # Platform.position.z is the walkable/top course used by Scene rendering and
    # stair connectivity; slab thickness occupies space below that level.
    return SceneObjectEnvelope(
        object_id=platform.id,
        object_kind="platform",
        geometry_known=True,
        x_min=platform.position.x,
        x_max=platform.position.x + platform.width,
        y_min=platform.position.y,
        y_max=platform.position.y + platform.depth,
        z_min=platform.position.z - platform.thickness,
        z_max=platform.position.z,
    )


def scene_object_envelopes(scene) -> tuple[SceneObjectEnvelope, ...]:
    """Return supported envelopes in stable ID order without mutating ``scene``."""
    envelopes = [
        *(_volume_envelope(volume) for volume in scene.volumes),
        *(_platform_envelope(platform) for platform in scene.platforms),
    ]
    return tuple(sorted(envelopes, key=lambda item: item.object_id))


def _known_bounds(envelope: SceneObjectEnvelope) -> tuple[float, float, float, float, float, float] | None:
    values = (
        envelope.x_min,
        envelope.x_max,
        envelope.y_min,
        envelope.y_max,
        envelope.z_min,
        envelope.z_max,
    )
    if not envelope.geometry_known or any(value is None for value in values):
        return None
    return values  # type: ignore[return-value]


def _gap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, max(a0, b0) - min(a1, b1))


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def _contains(
    outer: tuple[float, float, float, float, float, float],
    inner: tuple[float, float, float, float, float, float],
) -> bool:
    return (
        outer[0] <= inner[0] + CONNECTIVITY_TOLERANCE_M
        and outer[1] >= inner[1] - CONNECTIVITY_TOLERANCE_M
        and outer[2] <= inner[2] + CONNECTIVITY_TOLERANCE_M
        and outer[3] >= inner[3] - CONNECTIVITY_TOLERANCE_M
        and outer[4] <= inner[4] + CONNECTIVITY_TOLERANCE_M
        and outer[5] >= inner[5] - CONNECTIVITY_TOLERANCE_M
    )


def _pair_facts(subject: SceneObjectEnvelope, obj: SceneObjectEnvelope) -> SpatialPairFacts:
    first = _known_bounds(subject)
    second = _known_bounds(obj)
    if first is None or second is None:
        return SpatialPairFacts(
            subject_id=subject.object_id,
            object_id=obj.object_id,
            geometry_known=False,
        )

    ax0, ax1, ay0, ay1, az0, az1 = first
    bx0, bx1, by0, by1, bz0, bz1 = second
    x_gap = _gap(ax0, ax1, bx0, bx1)
    y_gap = _gap(ay0, ay1, by0, by1)
    z_gap = _gap(az0, az1, bz0, bz1)
    x_overlap = _overlap(ax0, ax1, bx0, bx1)
    y_overlap = _overlap(ay0, ay1, by0, by1)
    z_overlap = _overlap(az0, az1, bz0, bz1)

    overlaps_xy = x_overlap > EPSILON and y_overlap > EPSILON
    overlaps_3d = overlaps_xy and z_overlap > EPSILON

    # Face adjacency is deliberately stricter than generic proximity: one axis
    # is at/near a boundary while the other two have positive interior overlap.
    adjacent_face = (
        (x_gap <= CONNECTIVITY_TOLERANCE_M and x_overlap <= EPSILON and y_overlap > EPSILON and z_overlap > EPSILON)
        or (y_gap <= CONNECTIVITY_TOLERANCE_M and y_overlap <= EPSILON and x_overlap > EPSILON and z_overlap > EPSILON)
        or (z_gap <= CONNECTIVITY_TOLERANCE_M and z_overlap <= EPSILON and x_overlap > EPSILON and y_overlap > EPSILON)
    )

    return SpatialPairFacts(
        subject_id=subject.object_id,
        object_id=obj.object_id,
        geometry_known=True,
        x_gap=x_gap,
        y_gap=y_gap,
        z_gap=z_gap,
        x_overlap=x_overlap,
        y_overlap=y_overlap,
        z_overlap=z_overlap,
        left_of=ax1 <= bx0 + CONNECTIVITY_TOLERANCE_M,
        right_of=ax0 >= bx1 - CONNECTIVITY_TOLERANCE_M,
        # Canonical y grows from front toward rear.
        front_of=ay1 <= by0 + CONNECTIVITY_TOLERANCE_M,
        behind=ay0 >= by1 - CONNECTIVITY_TOLERANCE_M,
        above=az0 >= bz1 - CONNECTIVITY_TOLERANCE_M,
        below=az1 <= bz0 + CONNECTIVITY_TOLERANCE_M,
        overlaps_xy=overlaps_xy,
        overlaps_3d=overlaps_3d,
        adjacent_face=adjacent_face,
        contains_object=_contains(first, second),
        contained_by_object=_contains(second, first),
    )


def analyze_scene_spatial_relations(scene) -> SpatialRelationReport:
    """Derive deterministic pairwise spatial facts for supported Scene objects."""
    envelopes = scene_object_envelopes(scene)
    pairs = [
        _pair_facts(subject, obj)
        for subject in envelopes
        for obj in envelopes
        if subject.object_id != obj.object_id
    ]
    pairs.sort(key=lambda item: (item.subject_id, item.object_id))
    return SpatialRelationReport(
        scene_id=scene.id,
        envelopes=list(envelopes),
        pairs=pairs,
    )
