"""Generate framed-glazing parts from an explicit opening representation plan."""
from __future__ import annotations

from pydantic import BaseModel

from brickhouse.building.models import BuildingModel, Facade

from .building_layout import BuildingBrickShell
from .opening_motifs import opening_motif_by_id
from .opening_representation_plan import LEGORepresentationPlan
from .windows import WindowPartPlacement, _emit_pair, _selected_layout


class PlannedOpeningStatus(BaseModel):
    opening_id: str
    represented: bool
    reason: str | None = None


def generate_planned_opening_parts(
    building: BuildingModel,
    shell: BuildingBrickShell,
    plan: LEGORepresentationPlan,
) -> tuple[list[WindowPartPlacement], set[str], list[PlannedOpeningStatus]]:
    """Emit only exact reserved motifs; never fall back to fake glazing bricks."""
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
            statuses.append(PlannedOpeningStatus(opening_id=opening.id, represented=True))

    return placements, represented, statuses
