"""Deterministic architectural LEGO solution search.

This module sits between architectural truth and brick filling.  It does not
mutate BuildingModel/ArchitecturalScene geometry.  Instead it ranks small,
placement-approved LEGO assembly families that may become local representation
anchors before surrounding wall cells are filled.

The first supported family is deliberately narrow: validated window frame/pane
assemblies already approved by :mod:`brickhouse.bricks.windows`.  More
architectural families must be added explicitly rather than inferred from the
raw piece catalogue.
"""
from __future__ import annotations

from math import log
from typing import Literal

from pydantic import BaseModel, Field

from .windows import VALIDATED_WINDOW_ASSEMBLIES, WindowAssemblyDefinition

WindowComposition = Literal["single", "paired", "four_pane"]

# Physical LEGO proportions used elsewhere by BrickHouse: one stud is 8 mm and
# one standard brick course is 9.6 mm high.
STUD_MM = 8.0
BRICK_COURSE_MM = 9.6


class ArchitecturalWindowSolution(BaseModel):
    """One candidate LEGO representation for an architectural opening."""

    composition: WindowComposition
    assembly_id: str
    module_count: int = Field(gt=0)
    width_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)
    leaf_count: int = Field(gt=0)
    pane_count: int = Field(gt=0)
    aspect_ratio_error: float = Field(ge=0)
    topology_penalty: float = Field(ge=0)
    grid_adjustment_studs: int = Field(ge=0)
    grid_adjustment_bricks: int = Field(ge=0)
    score: float = Field(ge=0)


class ArchitecturalWindowSelection(BaseModel):
    """Ranked candidate set; the architectural source remains immutable."""

    architectural_width_m: float = Field(gt=0)
    architectural_height_m: float = Field(gt=0)
    raster_width_studs: int = Field(gt=0)
    raster_height_bricks: int = Field(gt=0)
    candidates: list[ArchitecturalWindowSolution]
    recommended: ArchitecturalWindowSolution | None = None


def _composition_geometry(
    assembly: WindowAssemblyDefinition,
    composition: WindowComposition,
) -> tuple[int, int, int, int, int]:
    """Return module_count, width, height, leaves and panes for one family."""
    if composition == "single":
        return 1, assembly.width_studs, assembly.height_bricks, 1, 1
    if composition == "paired":
        return 2, assembly.width_studs * 2, assembly.height_bricks, 2, 2
    return 4, assembly.width_studs * 2, assembly.height_bricks * 2, 2, 4


def _aspect_ratio_error(
    architectural_width_m: float,
    architectural_height_m: float,
    width_studs: int,
    height_bricks: int,
) -> float:
    architectural_ratio = architectural_width_m / architectural_height_m
    lego_ratio = (width_studs * STUD_MM) / (height_bricks * BRICK_COURSE_MM)
    # Log-ratio distance treats reciprocal over/under distortion symmetrically.
    return abs(log(lego_ratio / architectural_ratio))


def _topology_penalty(
    *,
    leaf_count: int,
    pane_count: int,
    observed_leaf_count: int | None,
    observed_pane_count: int | None,
) -> float:
    penalty = 0.0
    if observed_leaf_count is not None:
        penalty += abs(leaf_count - observed_leaf_count)
    if observed_pane_count is not None:
        penalty += abs(pane_count - observed_pane_count)
    return penalty


def rank_window_solutions(
    *,
    architectural_width_m: float,
    architectural_height_m: float,
    raster_width_studs: int,
    raster_height_bricks: int,
    observed_leaf_count: int | None = None,
    observed_pane_count: int | None = None,
    max_local_adjustment_studs: int = 1,
    max_local_adjustment_bricks: int = 1,
) -> ArchitecturalWindowSelection:
    """Rank catalog-backed window solutions without changing source geometry.

    ``raster_*`` describes the current global-grid projection.  Candidates may
    differ by a small, explicit local amount so a characteristic opening can be
    considered as a future wall-fill anchor.  This function only reports that
    adjustment; callers must never rewrite architectural measurements with it.
    """
    if architectural_width_m <= 0 or architectural_height_m <= 0:
        raise ValueError("architectural opening dimensions must be positive")
    if raster_width_studs <= 0 or raster_height_bricks <= 0:
        raise ValueError("raster opening dimensions must be positive")
    if max_local_adjustment_studs < 0 or max_local_adjustment_bricks < 0:
        raise ValueError("local adjustment bounds must be non-negative")
    if observed_leaf_count is not None and observed_leaf_count <= 0:
        raise ValueError("observed_leaf_count must be positive when provided")
    if observed_pane_count is not None and observed_pane_count <= 0:
        raise ValueError("observed_pane_count must be positive when provided")

    candidates: list[ArchitecturalWindowSolution] = []
    for assembly in VALIDATED_WINDOW_ASSEMBLIES:
        for composition in ("single", "paired", "four_pane"):
            module_count, width, height, leaves, panes = _composition_geometry(assembly, composition)
            dx = abs(width - raster_width_studs)
            dz = abs(height - raster_height_bricks)
            if dx > max_local_adjustment_studs or dz > max_local_adjustment_bricks:
                continue

            ratio_error = _aspect_ratio_error(
                architectural_width_m,
                architectural_height_m,
                width,
                height,
            )
            topology = _topology_penalty(
                leaf_count=leaves,
                pane_count=panes,
                observed_leaf_count=observed_leaf_count,
                observed_pane_count=observed_pane_count,
            )
            # Identity of the opening dominates.  Grid movement is a smaller
            # representation cost and is never allowed outside the explicit
            # local bounds above.
            score = 4.0 * ratio_error + 3.0 * topology + 0.35 * dx + 0.35 * dz
            candidates.append(
                ArchitecturalWindowSolution(
                    composition=composition,
                    assembly_id=assembly.id,
                    module_count=module_count,
                    width_studs=width,
                    height_bricks=height,
                    leaf_count=leaves,
                    pane_count=panes,
                    aspect_ratio_error=ratio_error,
                    topology_penalty=topology,
                    grid_adjustment_studs=dx,
                    grid_adjustment_bricks=dz,
                    score=score,
                )
            )

    candidates.sort(
        key=lambda item: (
            item.score,
            item.grid_adjustment_studs + item.grid_adjustment_bricks,
            item.module_count,
            item.assembly_id,
        )
    )
    return ArchitecturalWindowSelection(
        architectural_width_m=architectural_width_m,
        architectural_height_m=architectural_height_m,
        raster_width_studs=raster_width_studs,
        raster_height_bricks=raster_height_bricks,
        candidates=candidates,
        recommended=candidates[0] if candidates else None,
    )
