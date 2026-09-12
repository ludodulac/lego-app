"""Generate opening parts from an explicit LEGORepresentationPlan.

Curated reservations are authoritative for all opening semantics. A deliberately
narrow compatibility path remains for architectural WINDOWs only: when no curated
motif fits and no structured leaf/pane topology is known, the historical window
renderer may still emit its joinery-free glazing so existing M0 window behavior is
not silently lost. A DOOR with explicit structured glazing may likewise emit only
joinery-free glazing when no curated door motif fits: the glass is established,
while frame/leaf composition remains unknown and is therefore not invented.
UNKNOWN openings never use either fallback.
"""
from __future__ import annotations

import unicodedata

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
    _to_global,
    choose_window_layout,
)

_GENERIC_TWO_PANE_MOTIF_ID = "generic_two_pane:raster_split"
_COMPACT_TWO_PANE_MOTIF_ID = "compact_two_pane:transparent_panels"


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


def _normalized(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )


def _has_explicit_framed_glazing(opening) -> bool:
    """Return true only when structured evidence positively establishes glazing."""
    visual = opening.opening_visual
    if visual is None or visual.glazing is None:
        return False
    value = _normalized(visual.glazing)
    if not value:
        return False
    negative_tokens = (
        "none", "no glazing", "no glass", "not glazed", "unglazed",
        "sans vitrage", "sans verre", "non vitree", "opaque", "solid",
        "unknown", "inconnu", "indetermine", "glass block", "glass blocks",
        "pave de verre", "paves de verre",
    )
    return not any(token in value for token in negative_tokens)


def _emit_joinery_free_glazed_door(
    *,
    opening,
    raster,
    facade: Facade,
    front: int,
    depth: int,
    placements: list[WindowPartPlacement],
) -> bool:
    """Represent established door glazing without guessing leaves, panes, or frame."""
    if opening.type is not OpeningType.DOOR or not _has_explicit_framed_glazing(opening):
        return False
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


def _emit_generic_two_pane(
    *,
    raster,
    facade: Facade,
    front: int,
    depth: int,
    placements: list[WindowPartPlacement],
) -> bool:
    """Fill the exact raster as two glazed zones separated by one neutral mullion.

    The surrounding wall remains the jamb/lintel/sill support already owned by the
    wall raster. Only the central subdivision is added, so pane_count=2 is visible
    without inventing leaf count or a window style. The same placement-approved
    BRICK_1X1 primitive used by joinery-free glazing is reused for the mullion.
    """
    if raster.width_studs < 5 or raster.height_bricks < 2:
        return False
    mullion_local_x = raster.width_studs // 2
    left_width = mullion_local_x
    right_width = raster.width_studs - mullion_local_x - 1
    if left_width < 1 or right_width < 1:
        return False

    _emit_joinery_free_glazing(
        placements,
        facade=facade,
        local_x=raster.x_studs,
        z_bricks=raster.z_bricks,
        width_studs=left_width,
        height_bricks=raster.height_bricks,
        front=front,
        depth=depth,
        opening_id=raster.id,
    )
    _emit_joinery_free_glazing(
        placements,
        facade=facade,
        local_x=raster.x_studs + mullion_local_x + 1,
        z_bricks=raster.z_bricks,
        width_studs=right_width,
        height_bricks=raster.height_bricks,
        front=front,
        depth=depth,
        opening_id=raster.id,
    )
    for dz in range(raster.height_bricks):
        x, y, z, rotation = _to_global(
            facade,
            raster.x_studs + mullion_local_x,
            1,
            raster.z_bricks + dz,
            front,
            depth,
        )
        placements.append(WindowPartPlacement(
            part_id="BRICK_1X1",
            category="window_frame",
            facade=facade,
            x_studs=x,
            y_studs=y,
            z_plates=z,
            rotation_quarter_turns=rotation,
            opening_id=raster.id,
        ))
    return True


def _compact_panel_heights(height_bricks: int) -> tuple[int, ...] | None:
    """Partition height into 3-brick panels and 2-brick slots; 2-brick slots use two clear 1-brick panels."""
    for count in range(1, 4):
        for twos in range(count + 1):
            threes = count - twos
            if 3 * threes + 2 * twos == height_bricks:
                return (3,) * threes + (2,) * twos
    return None


def _emit_compact_two_pane(
    *, raster, facade: Facade, front: int, depth: int, placements: list[WindowPartPlacement],
) -> bool:
    """Build two 4-stud transparent panel stacks with one neutral central mullion."""
    if raster.width_studs != 9:
        return False
    heights = _compact_panel_heights(raster.height_bricks)
    if heights is None:
        return False
    for pane_x in (0, 5):
        z_offset = 0
        for panel_height in heights:
            if panel_height == 3:
                x, y, z, rotation = _to_global(facade, raster.x_studs + pane_x, 4, raster.z_bricks + z_offset, front, depth)
                placements.append(WindowPartPlacement(part_id="PANEL_1X4X3_60581", category="window_pane", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=raster.id))
            else:
                for one_high in range(2):
                    x, y, z, rotation = _to_global(facade, raster.x_studs + pane_x, 4, raster.z_bricks + z_offset + one_high, front, depth)
                    placements.append(WindowPartPlacement(part_id="PANEL_1X4X1_43337", category="window_pane", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=raster.id))
            z_offset += panel_height
    for dz in range(raster.height_bricks):
        x, y, z, rotation = _to_global(facade, raster.x_studs + 4, 1, raster.z_bricks + dz, front, depth)
        placements.append(WindowPartPlacement(part_id="BRICK_1X1", category="window_frame", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=raster.id))
    return True


def generate_planned_opening_parts(
    building: BuildingModel,
    shell: BuildingBrickShell,
    plan: LEGORepresentationPlan,
) -> tuple[list[WindowPartPlacement], set[str], list[PlannedOpeningStatus]]:
    """Emit reserved motifs, with conservative evidence-backed fallbacks."""
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
                if _emit_joinery_free_glazed_door(
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
                        representation="joinery_free_glazed_door",
                        reason=reservation.reason or "no curated glazed-door motif fit",
                    ))
                    continue
                statuses.append(PlannedOpeningStatus(
                    opening_id=opening.id,
                    represented=False,
                    reason=reservation.reason or "opening has no reserved motif",
                ))
                continue

            if reservation.motif_id == _COMPACT_TWO_PANE_MOTIF_ID:
                if (reservation.width_studs != raster.width_studs or reservation.height_bricks != raster.height_bricks or not _emit_compact_two_pane(raster=raster, facade=facade, front=front, depth=depth, placements=placements)):
                    statuses.append(PlannedOpeningStatus(opening_id=opening.id, represented=False, reason="compact two-pane reservation does not match a representable wall raster"))
                    continue
                represented.add(opening.id)
                statuses.append(PlannedOpeningStatus(opening_id=opening.id, represented=True, representation="compact_two_pane", reason=reservation.reason))
                continue

            if reservation.motif_id == _GENERIC_TWO_PANE_MOTIF_ID:
                if (
                    reservation.width_studs != raster.width_studs
                    or reservation.height_bricks != raster.height_bricks
                    or not _emit_generic_two_pane(
                        raster=raster,
                        facade=facade,
                        front=front,
                        depth=depth,
                        placements=placements,
                    )
                ):
                    statuses.append(PlannedOpeningStatus(
                        opening_id=opening.id,
                        represented=False,
                        reason="generic two-pane reservation does not match a representable wall raster",
                    ))
                    continue
                represented.add(opening.id)
                statuses.append(PlannedOpeningStatus(
                    opening_id=opening.id,
                    represented=True,
                    representation="generic_two_pane",
                    reason=reservation.reason,
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
