"""Explicit LEGO representation planning for architectural openings.

Architectural semantics stay upstream. This module chooses only among curated,
placement-approved framed-glazing motifs and reserves their exact LEGO footprint
before wall infill. A DOOR remains a DOOR and an UNKNOWN opening remains UNKNOWN;
LEGO convenience never reclassifies either one.
"""
from __future__ import annotations

from math import log
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade, OpeningType

from .architectural_solutions import select_facade_window_solutions
from .building_layout import BuildingBrickShell
from .opening_motifs import (
    OpeningMotif,
    OpeningMotifComposition,
    OpeningMotifOrientation,
    OpeningMotifSupportRequirement,
    OpeningRepresentationRole,
    opening_motif_by_id,
    opening_motifs_for_representation,
)


PlanStatus = Literal["reserved", "unsupported", "not_applicable"]


class OpeningRepresentationReservation(BaseModel):
    opening_id: str
    facade: Facade
    architectural_type: OpeningType
    status: PlanStatus
    representation_role: OpeningRepresentationRole | None = None
    motif_id: str | None = None
    composition: OpeningMotifComposition | None = None
    assembly_id: str | None = None
    width_studs: int | None = Field(default=None, gt=0)
    height_bricks: int | None = Field(default=None, gt=0)
    depth_studs: int | None = Field(default=None, gt=0)
    orientation: OpeningMotifOrientation | None = None
    connection_strategy: str | None = None
    support_requirement: OpeningMotifSupportRequirement | None = None
    reason: str | None = None


class LEGORepresentationPlan(BaseModel):
    """Supplier-independent reservations selected before wall brick filling."""

    building_id: str
    volume_id: str
    openings: list[OpeningRepresentationReservation] = Field(default_factory=list)

    @property
    def blockers(self) -> list[OpeningRepresentationReservation]:
        return [item for item in self.openings if item.status == "unsupported"]

    def reservation(self, opening_id: str) -> OpeningRepresentationReservation | None:
        return next((item for item in self.openings if item.opening_id == opening_id), None)


def _structured_glazing_present(opening) -> bool | None:
    visual = opening.opening_visual
    if visual is None or visual.glazing is None:
        return None
    value = " ".join(visual.glazing.lower().replace("_", " ").replace("-", " ").split())
    if not value:
        return False
    negative = {
        "none", "no glazing", "no glass", "not glazed", "unglazed",
        "sans vitrage", "sans verre", "non vitree", "opaque", "solid",
        "unknown", "inconnu", "indetermine",
    }
    return value not in negative


def _representation_role(opening) -> OpeningRepresentationRole | None:
    if opening.type is OpeningType.WINDOW:
        return "window"
    glazing = _structured_glazing_present(opening)
    if opening.type is OpeningType.DOOR and glazing is True:
        return "glazed_door"
    if opening.type is OpeningType.UNKNOWN and glazing is True:
        return "neutral_glazed"
    return None


def _topology(opening) -> tuple[int | None, int | None]:
    visual = opening.opening_visual
    if visual is None:
        return None, None
    return visual.leaf_count, visual.pane_count


def _score_motif(opening, raster, motif: OpeningMotif, *, studs_per_meter: float, courses_per_meter: float) -> tuple[float, int, int, str]:
    metric_ratio = opening.width / opening.height
    lego_ratio = (motif.width_studs / studs_per_meter) / (motif.height_bricks / courses_per_meter)
    ratio_error = abs(log(lego_ratio / metric_ratio))
    dx = abs(motif.width_studs - raster.width_studs)
    dz = abs(motif.height_bricks - raster.height_bricks)
    return 4.0 * ratio_error + 0.35 * dx + 0.35 * dz, dx, dz, motif.id


def _best_non_window_motif(opening, raster, wall) -> OpeningMotif | None:
    role = _representation_role(opening)
    if role not in {"glazed_door", "neutral_glazed"}:
        return None
    leaves, panes = _topology(opening)
    candidates = opening_motifs_for_representation(
        representation_role=role,
        leaf_count=leaves,
        pane_count=panes,
    )
    bounded = [
        motif for motif in candidates
        if abs(motif.width_studs - raster.width_studs) <= 1
        and abs(motif.height_bricks - raster.height_bricks) <= 1
    ]
    if not bounded:
        return None
    return min(
        bounded,
        key=lambda motif: _score_motif(
            opening,
            raster,
            motif,
            studs_per_meter=wall.grid.studs_per_meter,
            courses_per_meter=wall.grid.courses_per_meter,
        ),
    )


def _reserved(opening, motif: OpeningMotif) -> OpeningRepresentationReservation:
    return OpeningRepresentationReservation(
        opening_id=opening.id,
        facade=opening.facade,
        architectural_type=opening.type,
        status="reserved",
        representation_role=motif.representation_role,
        motif_id=motif.id,
        composition=motif.composition,
        assembly_id=motif.assembly_id,
        width_studs=motif.width_studs,
        height_bricks=motif.height_bricks,
        depth_studs=motif.depth_studs,
        orientation=motif.orientation,
        connection_strategy=motif.connection_strategy,
        support_requirement=motif.support_requirement,
    )


def _unsupported(opening, role: OpeningRepresentationRole | None, reason: str) -> OpeningRepresentationReservation:
    return OpeningRepresentationReservation(
        opening_id=opening.id,
        facade=opening.facade,
        architectural_type=opening.type,
        status="unsupported",
        representation_role=role,
        reason=reason,
    )


def build_opening_representation_plan(
    building: BuildingModel,
    shell: BuildingBrickShell,
) -> LEGORepresentationPlan:
    """Choose exact motif footprints without mutating architecture or wall geometry."""
    source_openings = [item for item in building.openings if item.volume_id == shell.volume_id]
    by_id = {item.id: item for item in source_openings}
    rasters = {
        raster.id: (wall, raster)
        for wall in shell.walls
        for raster in wall.grid.openings
    }
    reservations: dict[str, OpeningRepresentationReservation] = {}

    # Preserve the existing facade-coherent window selection rather than
    # regressing to independent per-window choices.
    for wall in shell.walls:
        selection = select_facade_window_solutions(
            facade=wall.facade,
            openings=building.openings,
            shell=shell,
        )
        if selection is None:
            continue
        for choice in selection.choices:
            opening = by_id.get(choice.opening_id)
            motif = opening_motif_by_id(choice.solution.motif_id)
            if opening is not None and motif is not None:
                reservations[opening.id] = _reserved(opening, motif)

    for opening in sorted(source_openings, key=lambda item: item.id):
        if opening.id in reservations:
            continue
        role = _representation_role(opening)
        wall_and_raster = rasters.get(opening.id)
        if wall_and_raster is None:
            reservations[opening.id] = _unsupported(
                opening,
                role,
                "opening has no reserved wall raster in the target volume",
            )
            continue

        if opening.type is OpeningType.WINDOW:
            reservations[opening.id] = _unsupported(
                opening,
                "window",
                "no curated window motif fits the bounded local raster and known composition",
            )
            continue

        if role is None:
            if opening.type is OpeningType.DOOR:
                reason = "door glazing is not established by structured evidence"
            elif opening.type is OpeningType.UNKNOWN:
                reason = "unknown opening lacks structured glazing evidence; semantic subtype remains unresolved"
            else:
                reason = f"opening type {opening.type.value!r} has no validated architectural motif"
            reservations[opening.id] = OpeningRepresentationReservation(
                opening_id=opening.id,
                facade=opening.facade,
                architectural_type=opening.type,
                status="not_applicable" if opening.type is OpeningType.GARAGE_DOOR else "unsupported",
                reason=reason,
            )
            continue

        wall, raster = wall_and_raster
        motif = _best_non_window_motif(opening, raster, wall)
        if motif is None:
            reservations[opening.id] = _unsupported(
                opening,
                role,
                "no curated framed-glazing motif fits the bounded local raster and known composition",
            )
        else:
            reservations[opening.id] = _reserved(opening, motif)

    return LEGORepresentationPlan(
        building_id=building.id,
        volume_id=shell.volume_id,
        openings=[reservations[item.id] for item in sorted(source_openings, key=lambda item: item.id)],
    )
