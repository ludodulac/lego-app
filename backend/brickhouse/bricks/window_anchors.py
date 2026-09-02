"""Apply architectural window selections to the LEGO wall grid only.

Architectural measurements remain immutable. This module creates a derived LEGO
shell whose opening voids may move/resize by the small bounds already approved by
architectural solution selection, then regenerates wall fill around those voids.
"""
from __future__ import annotations

from math import ceil, floor
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade
from .architectural_solutions import select_facade_window_solutions
from .building_layout import BuildingBrickShell
from .placement import WallOpeningGrid, generate_wall_layout_with_openings


class AppliedWindowAnchor(BaseModel):
    opening_id: str
    facade: Facade
    composition: Literal["single", "paired", "four_pane"]
    assembly_id: str
    source_x_studs: int = Field(ge=0)
    source_z_bricks: int = Field(ge=0)
    source_width_studs: int = Field(gt=0)
    source_height_bricks: int = Field(gt=0)
    anchored_x_studs: int = Field(ge=0)
    anchored_z_bricks: int = Field(ge=0)
    anchored_width_studs: int = Field(gt=0)
    anchored_height_bricks: int = Field(gt=0)

    @property
    def geometry_changed(self) -> bool:
        return (
            self.source_x_studs != self.anchored_x_studs
            or self.source_z_bricks != self.anchored_z_bricks
            or self.source_width_studs != self.anchored_width_studs
            or self.source_height_bricks != self.anchored_height_bricks
        )


class WindowAnchorApplication(BaseModel):
    shell: BuildingBrickShell
    anchors: list[AppliedWindowAnchor] = Field(default_factory=list)
    rejected_facades: list[Facade] = Field(default_factory=list)


def _best_start(
    *,
    metric_offset: float,
    metric_size: float,
    units_per_meter: float,
    span_units: int,
    wall_span_units: int,
    source_start: int,
) -> int:
    """Place a selected span nearest the architectural centre, deterministically."""
    target_center = (metric_offset + metric_size / 2.0) * units_per_meter
    raw_start = target_center - span_units / 2.0
    starts = {
        source_start,
        floor(raw_start),
        ceil(raw_start),
        round(raw_start),
    }
    valid = [start for start in starts if 0 <= start <= wall_span_units - span_units]
    if not valid:
        return min(max(round(raw_start), 0), wall_span_units - span_units)
    return min(
        valid,
        key=lambda start: (
            abs((start + span_units / 2.0) - target_center),
            abs(start - source_start),
            start,
        ),
    )


def apply_architectural_window_anchors(
    building: BuildingModel,
    shell: BuildingBrickShell,
) -> WindowAnchorApplication:
    """Return a LEGO-derived shell with facade-consistent window anchors applied.

    A facade is atomic: if the proposed openings overlap, exceed the wall, or
    otherwise fail the existing wall-layout validator, that facade keeps its
    original raster rather than partially applying a misleading solution.
    """
    openings = {
        opening.id: opening
        for opening in building.openings
        if opening.volume_id == shell.volume_id
    }
    updated_walls = []
    applied: list[AppliedWindowAnchor] = []
    rejected: list[Facade] = []

    for wall in shell.walls:
        selection = select_facade_window_solutions(
            facade=wall.facade,
            openings=building.openings,
            shell=shell,
        )
        if selection is None:
            updated_walls.append(wall)
            continue

        choice_by_id = {choice.opening_id: choice for choice in selection.choices}
        proposed_openings: list[WallOpeningGrid] = []
        facade_anchors: list[AppliedWindowAnchor] = []
        for raster in wall.grid.openings:
            choice = choice_by_id.get(raster.id)
            opening = openings.get(raster.id)
            if choice is None or opening is None:
                proposed_openings.append(raster)
                continue

            solution = choice.solution
            x = _best_start(
                metric_offset=opening.offset_horizontal,
                metric_size=opening.width,
                units_per_meter=wall.grid.studs_per_meter,
                span_units=solution.width_studs,
                wall_span_units=wall.grid.width_studs,
                source_start=raster.x_studs,
            )
            z = _best_start(
                metric_offset=opening.offset_vertical,
                metric_size=opening.height,
                units_per_meter=wall.grid.courses_per_meter,
                span_units=solution.height_bricks,
                wall_span_units=wall.grid.height_bricks,
                source_start=raster.z_bricks,
            )
            anchored = raster.model_copy(update={
                "x_studs": x,
                "z_bricks": z,
                "width_studs": solution.width_studs,
                "height_bricks": solution.height_bricks,
            })
            proposed_openings.append(anchored)
            facade_anchors.append(AppliedWindowAnchor(
                opening_id=opening.id,
                facade=wall.facade,
                composition=solution.composition,
                assembly_id=solution.assembly_id,
                source_x_studs=raster.x_studs,
                source_z_bricks=raster.z_bricks,
                source_width_studs=raster.width_studs,
                source_height_bricks=raster.height_bricks,
                anchored_x_studs=x,
                anchored_z_bricks=z,
                anchored_width_studs=solution.width_studs,
                anchored_height_bricks=solution.height_bricks,
            ))

        try:
            layout = generate_wall_layout_with_openings(
                width_studs=wall.grid.width_studs,
                height_bricks=wall.grid.height_bricks,
                openings=proposed_openings,
            )
        except ValueError:
            rejected.append(wall.facade)
            updated_walls.append(wall)
            continue

        grid = wall.grid.model_copy(update={"openings": proposed_openings})
        updated_walls.append(wall.model_copy(update={"grid": grid, "layout": layout}))
        applied.extend(facade_anchors)

    return WindowAnchorApplication(
        shell=shell.model_copy(update={"walls": updated_walls}),
        anchors=applied,
        rejected_facades=rejected,
    )
