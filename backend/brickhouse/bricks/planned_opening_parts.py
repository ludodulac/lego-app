"""Generate opening parts from an explicit LEGORepresentationPlan.

Curated reservations are authoritative for all opening semantics. A deliberately
narrow compatibility path remains for architectural WINDOWs only: when no curated
motif fits and no structured leaf/pane topology is known, the historical window
renderer may still emit its joinery-free glazing so existing M0 window behavior is
not silently lost. DOOR and UNKNOWN openings never use that fallback.
"""
from __future__ import annotations

from pydantic import BaseModel

from brickhouse.building.models import BuildingModel, Facade, OpeningType, WindowStyle

from .building_layout import BuildingBrickShell
from .opening_motifs import opening_motif_by_id
from .opening_representation_plan import LEGORepresentationPlan
from .windows import (
    WindowPartPlacement,
    _emit_joinery_free_glazing,
    _emit_pair,
    _selected_layout,
    choose_window_layout,
)


class PlannedOpeningStatus(BaseModel):
    opening_id: str
    represented: bool
    representation: str | None = None
    reason: str | None = None


def _has_structured_topology(opening) -> bool:
    visual = opening.opening_visual
    return visual is not None and (
        visual.leaf_count is not None or visual.pane_count is not None
    )


def _emit_legacy_window_fallback(
    *,
    opening,
    raster,
    facade: Facade,
    front: int,
    depth: int,
    placements: list[WindowPartPlacement],
) -> bool:
    """Preserve old WINDOW rendering only where it cannot contradict known topology."""
    if opening.type is not OpeningType.WINDOW or _has_structured_topology(opening):
        return False

    style = opening.window_style or WindowStyle.SIMPLE
    layout = choose_window_layout(style, raster.width_studs, raster.height_bricks)
    if layout:
        for assembly, x_offset, z_offset in layout:
            _emit_pair(
                placements,
                assembly,
                facade,
                raster.x_studs + x_offset,
                raster.z_bricks + z_offset,
                front,
                depth,
                opening_id=raster.id,
            )
        return True

    if style in {WindowStyle.SIMPLE, WindowStyle.TRADITIONAL_TALL}:
        _emit_joinery_free_glazing(
            placements,
            facade=facade,
            local_x=raster.x_studs,
            z_bricks=raster.z_bricks,
            width_studs=raster.width_studs,
            height_bricks=raster.height_bricks,
            front=front,
            depth=depth,
            opening_id=raster.id,
        )
        return True
    return False


def generate_planned_opening_parts(
    building: BuildingModel,
    shell: BuildingBrickShell,
    plan: LEGORepresentationPlan,
) -> tuple[list[WindowPartPlacement], set[str], list[PlannedOpeningStatus]]:
    """Emit reserved motifs, with a diagnosed compatibility fallback for WINDOW only."""
    if plan.building_id != building.id or plan.volume_id != shell.volume_id:
        raise ValueError("opening representation plan does not match building/shell")

    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    openings = {
        item.id: item
        for item in building.openings
        if item.volume_id == shell.volume_id
    }
    reservations = {item.opening_id: item for item in plan.openings}
    placements: list[WindowPartPlacement] = []
    represented: set[str] = set()
    statuses: list[PlannedOpeningStatus] = []

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        for raster in walls[facade].grid.openings:
            opening = openings.get(raster.id)
            reservation = reservations.get(raster.id)
            if opening is None or reservation is None:
                continue

            if reservation.status != "reserved":
                if _emit_legacy_window_fallback(
                    opening=opening,
                    raster=raster,
                    facade=facade,
                    front=front,
                    depth=depth,
                    placements=placements,
                ):
                    represented.add(opening.id)
                    statuses.append(PlannedOpeningStatus(
                        opening_id=opening.id,
                        represented=True,
                        representation="legacy_window_fallback",
                        reason=reservation.reason or "no curated window motif fit",
                    ))
                    continue
                statuses.append(PlannedOpeningStatus(
                    opening_id=opening.id,
                    represented=False,
                    reason=reservation.reason or "opening has no reserved motif",
                ))
                continue

            motif = opening_motif_by_id(reservation.motif_id or "")
            if motif is None:
                statuses.append(PlannedOpeningStatus(
                    opening_id=opening.id,
                    represented=False,
                    reason="reserved motif is not present in the curated registry",
                ))
                continue
            if raster.width_studs != motif.width_studs or raster.height_bricks != motif.height_bricks:
                statuses.append(PlannedOpeningStatus(
                    opening_id=opening.id,
                    represented=False,
                    reason="wall raster does not match the reserved motif footprint",
                ))
                continue

            layout = _selected_layout(
                motif.composition,
                motif.assembly_id,
                motif.width_studs,
                motif.height_bricks,
            )
            for assembly, x_offset, z_offset in layout:
                _emit_pair(
                    placements,
                    assembly,
                    facade,
                    raster.x_studs + x_offset,
                    raster.z_bricks + z_offset,
                    front,
                    depth,
                    opening_id=raster.id,
                )
            represented.add(opening.id)
            statuses.append(PlannedOpeningStatus(
                opening_id=opening.id,
                represented=True,
                representation="curated_motif",
            ))

    return placements, represented, statuses
