"""Deterministic representation-only raster selection for gable roofs.

This module exposes only the LEGO span adjustments that remain after preserving
architectural roof extents. Architectural geometry stays immutable: declared
overhang is a raster target, while any additional catalog quantization is
reported separately as representation-only fidelity information.
"""
from __future__ import annotations

from math import atan2, degrees

from pydantic import BaseModel, Field

from brickhouse.building.models import RidgeDirection
from brickhouse.geometry.models import BuildingGeometry

from .building_layout import BuildingBrickShell
from .roof import (
    _architectural_overhang_studs,
    _connected_roof_span,
    _gable_planes,
    _plane_run_and_rise,
    _shared_tileable_line_length,
    select_roof_slope_family,
)


class GableRoofRasterSelection(BaseModel):
    roof_id: str
    ridge_direction: RidgeDirection
    slope_family_id: str
    target_pitch_degrees: float = Field(gt=0, lt=90)
    selected_pitch_degrees: float = Field(gt=0, lt=90)
    wall_span_studs: int = Field(gt=0)
    architectural_span_studs: int = Field(gt=0)
    selected_span_studs: int = Field(gt=0)
    wall_line_length_studs: int = Field(gt=0)
    architectural_line_length_studs: int = Field(gt=0)
    selected_line_length_studs: int = Field(gt=0)

    @property
    def declared_span_overhang_studs(self) -> int:
        return self.architectural_span_studs - self.wall_span_studs

    @property
    def declared_line_overhang_studs(self) -> int:
        return self.architectural_line_length_studs - self.wall_line_length_studs

    @property
    def span_adjustment_studs(self) -> int:
        return self.selected_span_studs - self.architectural_span_studs

    @property
    def line_adjustment_studs(self) -> int:
        return self.selected_line_length_studs - self.architectural_line_length_studs

    @property
    def geometry_changed(self) -> bool:
        return self.span_adjustment_studs != 0 or self.line_adjustment_studs != 0


def select_gable_roof_raster(
    geometry: BuildingGeometry,
    shell: BuildingBrickShell,
) -> GableRoofRasterSelection:
    """Return the exact architectural target and catalog raster used by the roof engine."""
    negative, _ = _gable_planes(geometry, shell.volume_id)
    run, rise = _plane_run_and_rise(negative)
    target_pitch = degrees(atan2(rise, run))
    family = select_roof_slope_family(target_pitch)
    direction = negative.ridge_direction
    assert direction is not None

    width = next(
        record.grid.width_studs
        for record in shell.walls
        if record.facade.value == "front"
    )
    depth = next(
        record.grid.width_studs
        for record in shell.walls
        if record.facade.value == "right"
    )
    wall_span, wall_line_length = (
        (width, depth)
        if direction is RidgeDirection.DEPTH
        else (depth, width)
    )
    run_negative, run_positive, line_negative, line_positive = (
        _architectural_overhang_studs(geometry, shell, direction)
    )
    architectural_span = wall_span + run_negative + run_positive
    architectural_line_length = wall_line_length + line_negative + line_positive
    selected_span = _connected_roof_span(
        wall_span, family, run_negative, run_positive
    )
    selected_line_length = _shared_tileable_line_length(
        architectural_line_length, family
    )

    return GableRoofRasterSelection(
        roof_id=negative.roof_id,
        ridge_direction=direction,
        slope_family_id=family.id,
        target_pitch_degrees=target_pitch,
        selected_pitch_degrees=family.pitch_degrees,
        wall_span_studs=wall_span,
        architectural_span_studs=architectural_span,
        selected_span_studs=selected_span,
        wall_line_length_studs=wall_line_length,
        architectural_line_length_studs=architectural_line_length,
        selected_line_length_studs=selected_line_length,
    )
