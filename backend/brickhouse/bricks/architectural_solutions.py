"""Deterministic architectural LEGO solution search.

This module sits between architectural truth and brick filling. It does not
mutate BuildingModel/ArchitecturalScene geometry. Instead it ranks small,
placement-approved LEGO assembly families that may become local representation
anchors before surrounding wall cells are filled.

The first supported family is deliberately narrow: validated window frame/pane
assemblies already approved by :mod:`brickhouse.bricks.windows`. More
architectural families must be added explicitly rather than inferred from the
raw piece catalogue.
"""
from __future__ import annotations

from itertools import product
from math import log
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade, Opening, OpeningType, WindowStyle
from .building_layout import BuildingBrickShell
from .windows import VALIDATED_WINDOW_ASSEMBLIES, WindowAssemblyDefinition

WindowComposition = Literal["single", "paired", "four_pane"]

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


class FacadeWindowChoice(BaseModel):
    opening_id: str
    source_raster_width_studs: int = Field(gt=0)
    source_raster_height_bricks: int = Field(gt=0)
    solution: ArchitecturalWindowSolution


class FacadeWindowSelection(BaseModel):
    """Coherent window-family choice for one facade, without moving openings."""

    facade: Facade
    choices: list[FacadeWindowChoice]
    individual_score: float = Field(ge=0)
    proportion_penalty: float = Field(ge=0)
    family_penalty: float = Field(ge=0)
    score: float = Field(ge=0)


def _composition_geometry(
    assembly: WindowAssemblyDefinition,
    composition: WindowComposition,
) -> tuple[int, int, int, int, int]:
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


def _matches_observed_topology(
    *,
    leaf_count: int,
    pane_count: int,
    observed_leaf_count: int | None,
    observed_pane_count: int | None,
) -> bool:
    """Treat known opening topology as an invariant, not a scoring preference."""
    if observed_leaf_count is not None and leaf_count != observed_leaf_count:
        return False
    if observed_pane_count is not None and pane_count != observed_pane_count:
        return False
    return True


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
    """Rank catalog-backed window solutions without inventing subdivisions.

    In the absence of explicit topology evidence only a single-module window is
    considered. When leaf/pane evidence exists, every candidate must match every
    known count exactly. Unsupported structured topology therefore yields no LEGO
    candidate instead of allowing aspect ratio or grid fit to invent joinery.
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

    compositions: tuple[WindowComposition, ...] = (
        ("single",)
        if observed_leaf_count is None and observed_pane_count is None
        else ("single", "paired", "four_pane")
    )
    candidates: list[ArchitecturalWindowSolution] = []
    for assembly in VALIDATED_WINDOW_ASSEMBLIES:
        for composition in compositions:
            module_count, width, height, leaves, panes = _composition_geometry(assembly, composition)
            if not _matches_observed_topology(
                leaf_count=leaves,
                pane_count=panes,
                observed_leaf_count=observed_leaf_count,
                observed_pane_count=observed_pane_count,
            ):
                continue
            dx = abs(width - raster_width_studs)
            dz = abs(height - raster_height_bricks)
            if dx > max_local_adjustment_studs or dz > max_local_adjustment_bricks:
                continue
            ratio_error = _aspect_ratio_error(
                architectural_width_m, architectural_height_m, width, height
            )
            topology = _topology_penalty(
                leaf_count=leaves,
                pane_count=panes,
                observed_leaf_count=observed_leaf_count,
                observed_pane_count=observed_pane_count,
            )
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


def _opening_topology(opening: Opening) -> tuple[int | None, int | None]:
    visual = opening.opening_visual
    leaf_count = visual.leaf_count if visual else None
    pane_count = visual.pane_count if visual else None
    if leaf_count is not None or pane_count is not None:
        return leaf_count, pane_count
    style = opening.window_style
    if style in {WindowStyle.SIMPLE, WindowStyle.TRADITIONAL_TALL}:
        return 1, 1
    if style is WindowStyle.PAIRED:
        return 2, 2
    if style is WindowStyle.FOUR_PANE:
        return 2, 4
    return None, None


def _relative_proportion_penalty(
    openings: list[Opening],
    solutions: tuple[ArchitecturalWindowSolution, ...],
) -> float:
    """Compare pairwise relative dimensions, independent of absolute LEGO scale."""
    penalty = 0.0
    for first_index, first in enumerate(openings):
        for second_index in range(first_index + 1, len(openings)):
            second = openings[second_index]
            first_solution = solutions[first_index]
            second_solution = solutions[second_index]
            metric_width_ratio = first.width / second.width
            lego_width_ratio = first_solution.width_studs / second_solution.width_studs
            metric_height_ratio = first.height / second.height
            lego_height_ratio = first_solution.height_bricks / second_solution.height_bricks
            penalty += abs(log(lego_width_ratio / metric_width_ratio))
            penalty += abs(log(lego_height_ratio / metric_height_ratio))
    return penalty


def _family_penalty(
    openings: list[Opening],
    solutions: tuple[ArchitecturalWindowSolution, ...],
) -> float:
    """Prefer repeated LEGO families only for architecturally similar openings."""
    penalty = 0.0
    for first_index, first in enumerate(openings):
        for second_index in range(first_index + 1, len(openings)):
            second = openings[second_index]
            metric_ratio_delta = abs(log((first.width / first.height) / (second.width / second.height)))
            first_topology = _opening_topology(first)
            second_topology = _opening_topology(second)
            topology_matches = (
                first_topology == (None, None)
                or second_topology == (None, None)
                or first_topology == second_topology
            )
            if metric_ratio_delta <= 0.12 and topology_matches:
                first_solution = solutions[first_index]
                second_solution = solutions[second_index]
                if (
                    first_solution.assembly_id != second_solution.assembly_id
                    or first_solution.composition != second_solution.composition
                ):
                    penalty += 1.0
    return penalty


def select_facade_window_solutions(
    *,
    facade: Facade,
    openings: list[Opening],
    shell: BuildingBrickShell,
    max_candidates_per_opening: int = 4,
) -> FacadeWindowSelection | None:
    """Select window solutions jointly so facade proportions survive discretization.

    Only openings belonging to ``shell.volume_id`` participate. This matters for
    multi-volume buildings where several volumes can expose the same facade enum.
    The shell remains read-only at this stage.
    """
    if max_candidates_per_opening <= 0:
        raise ValueError("max_candidates_per_opening must be positive")
    windows = [
        opening for opening in openings
        if opening.volume_id == shell.volume_id
        and opening.facade is facade
        and opening.type is OpeningType.WINDOW
    ]
    if not windows:
        return None
    wall = next((record for record in shell.walls if record.facade is facade), None)
    if wall is None:
        raise ValueError(f"shell has no wall for facade {facade.value!r}")
    rasters = {raster.id: raster for raster in wall.grid.openings}

    ranked: list[tuple[Opening, object, list[ArchitecturalWindowSolution]]] = []
    for opening in windows:
        raster = rasters.get(opening.id)
        if raster is None:
            raise ValueError(f"shell has no raster opening for {opening.id!r}")
        leaf_count, pane_count = _opening_topology(opening)
        selection = rank_window_solutions(
            architectural_width_m=opening.width,
            architectural_height_m=opening.height,
            raster_width_studs=raster.width_studs,
            raster_height_bricks=raster.height_bricks,
            observed_leaf_count=leaf_count,
            observed_pane_count=pane_count,
        )
        candidates = selection.candidates[:max_candidates_per_opening]
        if not candidates:
            return None
        ranked.append((opening, raster, candidates))

    best: FacadeWindowSelection | None = None
    for combination in product(*(entry[2] for entry in ranked)):
        architectural_openings = [entry[0] for entry in ranked]
        individual = sum(solution.score for solution in combination)
        proportions = _relative_proportion_penalty(architectural_openings, combination)
        families = _family_penalty(architectural_openings, combination)
        total = individual + 2.0 * proportions + 0.6 * families
        candidate = FacadeWindowSelection(
            facade=facade,
            choices=[
                FacadeWindowChoice(
                    opening_id=opening.id,
                    source_raster_width_studs=raster.width_studs,
                    source_raster_height_bricks=raster.height_bricks,
                    solution=solution,
                )
                for (opening, raster, _), solution in zip(ranked, combination)
            ],
            individual_score=individual,
            proportion_penalty=proportions,
            family_penalty=families,
            score=total,
        )
        if best is None or candidate.score < best.score:
            best = candidate
    return best
