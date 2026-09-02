"""Conservative validation helpers for metric platform SupportPost geometry.

ArchitecturalScene remains authoritative. These helpers never add, move, widen or
extend supports; they only detect contradictions in already-declared metric
support geometry so LEGO rendering cannot hide them.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.scene.models import ArchitecturalScene

SUPPORT_LEVEL_TOLERANCE_M = 0.12


class PlatformSupportLevelMismatch(BaseModel):
    platform_id: str
    support_id: str
    support_top_m: float
    platform_level_m: float
    delta_m: float = Field(ge=0)


def validate_platform_support_footprints(scene: ArchitecturalScene) -> None:
    """Reject a declared support whose footprint lies outside its platform.

    Touching the platform boundary is accepted. A SupportPost is metric geometry,
    so silently projecting an unrelated/outside post underneath a platform would
    be a source-topology error rather than a LEGO approximation.
    """
    for platform in scene.platforms:
        px0 = platform.position.x
        px1 = px0 + platform.width
        py0 = platform.position.y
        py1 = py0 + platform.depth
        for support in platform.supports:
            sx0 = support.position.x
            sx1 = sx0 + support.width
            sy0 = support.position.y
            sy1 = sy0 + support.depth
            overlaps_x = min(px1, sx1) >= max(px0, sx0)
            overlaps_y = min(py1, sy1) >= max(py0, sy0)
            if not (overlaps_x and overlaps_y):
                raise ValueError(
                    f"platform {platform.id!r} support {support.id!r} lies outside "
                    "the platform footprint; declared SupportPost geometry must "
                    "overlap the platform it supports"
                )


def platform_support_level_mismatches(
    scene: ArchitecturalScene,
    *,
    tolerance_m: float = SUPPORT_LEVEL_TOLERANCE_M,
) -> list[PlatformSupportLevelMismatch]:
    """Report declared support tops that do not meet the platform level.

    This deliberately does not repair the geometry. A later fidelity layer can
    surface the mismatch while preserving the evidence-backed metric values.
    """
    if tolerance_m < 0:
        raise ValueError("tolerance_m must be non-negative")
    mismatches: list[PlatformSupportLevelMismatch] = []
    for platform in scene.platforms:
        for support in platform.supports:
            support_top = support.position.z + support.height
            delta = abs(support_top - platform.position.z)
            if delta > tolerance_m:
                mismatches.append(
                    PlatformSupportLevelMismatch(
                        platform_id=platform.id,
                        support_id=support.id,
                        support_top_m=support_top,
                        platform_level_m=platform.position.z,
                        delta_m=delta,
                    )
                )
    return mismatches
