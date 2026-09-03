"""Apply architectural window selections to the LEGO wall grid only.

Architectural measurements remain immutable. This module creates a derived LEGO
shell whose opening voids may move/resize by the small bounds already approved by
architectural solution selection, then regenerates wall fill around those voids.

Anchor positions are selected jointly per facade on both axes. This preserves the
relative composition of openings when independent nearest-centre rounding would
otherwise distort spacing or make an otherwise representable facade overlap.
"""
from __future__ import annotations

from itertools import product
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


def _matches_structured_topology(opening, solution) -> bool:
    """Refuse LEGO subdivisions that contradict structured opening evidence."""
    visual = opening.opening_visual
    if visual is None:
        return True
    if visual.leaf_count is not None and solution.leaf_count != visual.leaf_count:
        return False
    if visual.pane_count is not None and solution.pane_count != visual.pane_count:
        return False
    return True


def _candidate_starts(
    *,
    metric_offset: float,
    metric_size: float,
    units_per_meter: float,
    span_units: int,
    wall_span_units: int,
    source_start: int,
) -> tuple[int, ...]:
    """Return the small deterministic local-start vocabulary around one opening."""
    target_center = (metric_offset + metric_size / 2.0) * units_per_meter
    raw_start = target_center - span_units / 2.0
    starts = {
        source_start,
        floor(raw_start),
        ceil(raw_start),
        round(raw_start),
    }
    valid = sorted(start for start in starts if 0 <= start <= wall_span_units - span_units)
    if valid:
        return tuple(valid)
    return (min(max(round(raw_start), 0), wall_span_units - span_units),)


def _best_start(
    *,
    metric_offset: float,
    metric_size: float,
    units_per_meter: float,
    span_units: int,
    wall_span_units: int,
    source_start: int,
) -> int:
    """Place one selected span nearest the architectural centre, deterministically."""
    target_center = (metric_offset + metric_size / 2.0) * units_per_meter
    return min(
        _candidate_starts(
            metric_offset=metric_offset,
            metric_size=metric_size,
            units_per_meter=units_per_meter,
            span_units=span_units,
            wall_span_units=wall_span_units,
            source_start=source_start,
        ),
        key=lambda start: (
            abs((start + span_units / 2.0) - target_center),
            abs(start - source_start),
            start,
        ),
    )


def _vertical_intervals_overlap(
    first_z: int,
    first_height: int,
    second_z: int,
    second_height: int,
) -> bool:
    return first_z < second_z + second_height and second_z < first_z + first_height


def _select_joint_z_starts(
    *,
    records: list[tuple[object, WallOpeningGrid, int]],
    courses_per_meter: float,
    wall_height_bricks: int,
) -> dict[str, int] | None:
    """Choose facade-local Z anchors jointly while preserving row composition.

    ``records`` contains ``(Opening, source raster, selected height)``. Candidate
    starts use the same bounded local vocabulary as historical independent
    placement. The score combines individual centre error with pairwise vertical
    centre-distance error, preserving relative levels without changing source
    metrics or selected window dimensions.
    """
    if not records:
        return {}

    candidate_sets = [
        _candidate_starts(
            metric_offset=opening.offset_vertical,
            metric_size=opening.height,
            units_per_meter=courses_per_meter,
            span_units=selected_height,
            wall_span_units=wall_height_bricks,
            source_start=raster.z_bricks,
        )
        for opening, raster, selected_height in records
    ]
    target_centers = [
        (opening.offset_vertical + opening.height / 2.0) * courses_per_meter
        for opening, _, _ in records
    ]

    best_starts: tuple[int, ...] | None = None
    best_key: tuple[float, float, tuple[int, ...]] | None = None
    for starts in product(*candidate_sets):
        centers = [
            start + records[index][2] / 2.0
            for index, start in enumerate(starts)
        ]
        valid = True
        spacing_error = 0.0
        for first in range(len(records)):
            for second in range(first + 1, len(records)):
                metric_delta = target_centers[second] - target_centers[first]
                lego_delta = centers[second] - centers[first]
                if metric_delta > 0 and lego_delta <= 0:
                    valid = False
                    break
                if metric_delta < 0 and lego_delta >= 0:
                    valid = False
                    break
                spacing_error += abs(lego_delta - metric_delta)
            if not valid:
                break
        if not valid:
            continue

        center_error = sum(
            abs(center - target)
            for center, target in zip(centers, target_centers)
        )
        source_motion = sum(
            abs(start - records[index][1].z_bricks)
            for index, start in enumerate(starts)
        )
        key = (center_error + spacing_error, float(source_motion), tuple(starts))
        if best_key is None or key < best_key:
            best_key = key
            best_starts = tuple(starts)

    if best_starts is None:
        return None
    return {
        records[index][0].id: start
        for index, start in enumerate(best_starts)
    }


def _select_joint_x_starts(
    *,
    records: list[tuple[object, WallOpeningGrid, int, int, int]],
    studs_per_meter: float,
    wall_width_studs: int,
) -> dict[str, int] | None:
    """Choose facade-local X anchors jointly while preserving architectural composition.

    ``records`` contains ``(Opening, source raster, selected width, selected height,
    anchored z)``. Candidate X starts remain the same conservative local choices
    used by the historical independent placement. The joint score adds pairwise
    centre-distance error, so the LEGO facade preserves opening spacing as well as
    each individual centre. Openings whose selected vertical spans overlap may never
    overlap horizontally. Architectural order is also preserved; no candidate may
    swap left/right identity.
    """
    if not records:
        return {}

    candidate_sets = [
        _candidate_starts(
            metric_offset=opening.offset_horizontal,
            metric_size=opening.width,
            units_per_meter=studs_per_meter,
            span_units=selected_width,
            wall_span_units=wall_width_studs,
            source_start=raster.x_studs,
        )
        for opening, raster, selected_width, _, _ in records
    ]
    target_centers = [
        (opening.offset_horizontal + opening.width / 2.0) * studs_per_meter
        for opening, _, _, _, _ in records
    ]

    best_starts: tuple[int, ...] | None = None
    best_key: tuple[float, float, tuple[int, ...]] | None = None
    for starts in product(*candidate_sets):
        centers = [
            start + records[index][2] / 2.0
            for index, start in enumerate(starts)
        ]
        valid = True
        spacing_error = 0.0
        for first in range(len(records)):
            _, _, first_width, first_height, first_z = records[first]
            for second in range(first + 1, len(records)):
                _, _, second_width, second_height, second_z = records[second]
                metric_delta = target_centers[second] - target_centers[first]
                lego_delta = centers[second] - centers[first]
                if metric_delta > 0 and lego_delta <= 0:
                    valid = False
                    break
                if metric_delta < 0 and lego_delta >= 0:
                    valid = False
                    break
                if _vertical_intervals_overlap(
                    first_z,
                    first_height,
                    second_z,
                    second_height,
                ):
                    first_end = starts[first] + first_width
                    second_end = starts[second] + second_width
                    if starts[first] < second_end and starts[second] < first_end:
                        valid = False
                        break
                spacing_error += abs(lego_delta - metric_delta)
            if not valid:
                break
        if not valid:
            continue

        center_error = sum(
            abs(center - target)
            for center, target in zip(centers, target_centers)
        )
        source_motion = sum(
            abs(start - records[index][1].x_studs)
            for index, start in enumerate(starts)
        )
        key = (center_error + spacing_error, float(source_motion), tuple(starts))
        if best_key is None or key < best_key:
            best_key = key
            best_starts = tuple(starts)

    if best_starts is None:
        return None
    return {
        records[index][0].id: start
        for index, start in enumerate(best_starts)
    }


def apply_architectural_window_anchors(
    building: BuildingModel,
    shell: BuildingBrickShell,
) -> WindowAnchorApplication:
    """Return a LEGO-derived shell with facade-consistent window anchors applied.

    A facade is atomic: if the proposed openings overlap, exceed the wall, contradict
    structured opening topology, or otherwise fail the existing wall-layout validator,
    that facade keeps its original raster rather than partially applying a misleading
    solution.
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

        if any(
            (opening := openings.get(choice.opening_id)) is not None
            and not _matches_structured_topology(opening, choice.solution)
            for choice in selection.choices
        ):
            rejected.append(wall.facade)
            updated_walls.append(wall)
            continue

        choice_by_id = {choice.opening_id: choice for choice in selection.choices}
        vertical_records: list[tuple[object, WallOpeningGrid, int]] = []
        for raster in wall.grid.openings:
            choice = choice_by_id.get(raster.id)
            opening = openings.get(raster.id)
            if choice is None or opening is None:
                continue
            vertical_records.append((opening, raster, choice.solution.height_bricks))

        joint_z = _select_joint_z_starts(
            records=vertical_records,
            courses_per_meter=wall.grid.courses_per_meter,
            wall_height_bricks=wall.grid.height_bricks,
        )
        if joint_z is None:
            rejected.append(wall.facade)
            updated_walls.append(wall)
            continue

        joint_records: list[tuple[object, WallOpeningGrid, int, int, int]] = []
        for raster in wall.grid.openings:
            choice = choice_by_id.get(raster.id)
            opening = openings.get(raster.id)
            if choice is None or opening is None:
                continue
            solution = choice.solution
            joint_records.append(
                (
                    opening,
                    raster,
                    solution.width_studs,
                    solution.height_bricks,
                    joint_z[opening.id],
                )
            )

        joint_x = _select_joint_x_starts(
            records=joint_records,
            studs_per_meter=wall.grid.studs_per_meter,
            wall_width_studs=wall.grid.width_studs,
        )
        if joint_x is None:
            rejected.append(wall.facade)
            updated_walls.append(wall)
            continue

        proposed_openings: list[WallOpeningGrid] = []
        facade_anchors: list[AppliedWindowAnchor] = []
        for raster in wall.grid.openings:
            choice = choice_by_id.get(raster.id)
            opening = openings.get(raster.id)
            if choice is None or opening is None:
                proposed_openings.append(raster)
                continue

            solution = choice.solution
            x = joint_x[opening.id]
            z = joint_z[opening.id]
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
