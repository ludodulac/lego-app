"""Apply LEGORepresentationPlan opening reservations to the derived wall grid.

This is a representation-only mutation. Architectural opening metrics and semantic
types remain untouched; only the downstream LEGO wall voids are locally anchored
to the exact curated motif footprints selected by the plan.
"""
from __future__ import annotations

from itertools import combinations
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade

from .building_layout import BuildingBrickShell
from .opening_representation_plan import LEGORepresentationPlan, OpeningRepresentationRole
from .placement import WallOpeningGrid, generate_wall_layout_with_openings
from .window_anchors import _select_joint_x_starts, _select_joint_z_starts


MAX_OPENING_ANCHOR_TRANSLATION_UNITS = 1
MAX_OPENING_FOOTPRINT_DELTA_UNITS = 1

AdjustmentStatus = Literal["unchanged", "bounded"]
RejectionCode = Literal[
    "architectural_identity_mismatch",
    "architectural_order_not_preserved",
    "vertical_anchor_unsatisfied",
    "horizontal_anchor_unsatisfied",
    "adjustment_exceeds_local_bound",
    "facade_layout_invalid",
]


class AppliedOpeningAnchor(BaseModel):
    opening_id: str
    facade: Facade
    representation_role: OpeningRepresentationRole
    motif_id: str
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


class OpeningRepresentationAdjustment(BaseModel):
    """Machine-readable representation-only delta for one architectural opening."""

    opening_id: str
    facade: Facade
    status: AdjustmentStatus
    delta_x_studs: int
    delta_z_bricks: int
    delta_width_studs: int
    delta_height_bricks: int

    @classmethod
    def from_anchor(cls, anchor: AppliedOpeningAnchor) -> "OpeningRepresentationAdjustment":
        deltas = {
            "delta_x_studs": anchor.anchored_x_studs - anchor.source_x_studs,
            "delta_z_bricks": anchor.anchored_z_bricks - anchor.source_z_bricks,
            "delta_width_studs": anchor.anchored_width_studs - anchor.source_width_studs,
            "delta_height_bricks": anchor.anchored_height_bricks - anchor.source_height_bricks,
        }
        return cls(
            opening_id=anchor.opening_id,
            facade=anchor.facade,
            status="bounded" if any(deltas.values()) else "unchanged",
            **deltas,
        )

    @property
    def within_local_bounds(self) -> bool:
        return (
            abs(self.delta_x_studs) <= MAX_OPENING_ANCHOR_TRANSLATION_UNITS
            and abs(self.delta_z_bricks) <= MAX_OPENING_ANCHOR_TRANSLATION_UNITS
            and abs(self.delta_width_studs) <= MAX_OPENING_FOOTPRINT_DELTA_UNITS
            and abs(self.delta_height_bricks) <= MAX_OPENING_FOOTPRINT_DELTA_UNITS
        )


class OpeningPlanRejection(BaseModel):
    """Deterministic blocker explaining why a facade was left unchanged."""

    facade: Facade
    code: RejectionCode
    opening_ids: list[str] = Field(default_factory=list)
    severity: Literal["blocker"] = "blocker"
    reason: str


class OpeningPlanApplication(BaseModel):
    shell: BuildingBrickShell
    anchors: list[AppliedOpeningAnchor] = Field(default_factory=list)
    adjustments: list[OpeningRepresentationAdjustment] = Field(default_factory=list)
    rejected_facades: list[Facade] = Field(default_factory=list)
    rejections: list[OpeningPlanRejection] = Field(default_factory=list)


def _rejection(
    *,
    facade: Facade,
    code: RejectionCode,
    opening_ids: list[str],
    reason: str,
) -> OpeningPlanRejection:
    return OpeningPlanRejection(
        facade=facade,
        code=code,
        opening_ids=sorted(opening_ids),
        reason=reason,
    )


def _identity_is_preserved(wall, openings, reservations) -> bool:
    for opening_id, reservation in reservations.items():
        opening = openings.get(opening_id)
        if opening is None:
            return False
        if opening.facade is not wall.facade or reservation.facade is not wall.facade:
            return False
        if reservation.architectural_type is not opening.type:
            return False
    return True


def _architectural_order_is_preserved(
    anchors: list[AppliedOpeningAnchor],
    openings: dict[str, object],
) -> bool:
    """Reject inversion of known left/right or vertical level order.

    Horizontal identity may not collapse because two distinct side-by-side openings
    would become ambiguous. Vertical levels may quantize to the same course, matching
    the historical conservative Z solver, but may never invert.
    """
    by_id = {anchor.opening_id: anchor for anchor in anchors}
    for first_id, second_id in combinations(sorted(by_id), 2):
        first_opening = openings[first_id]
        second_opening = openings[second_id]
        first_anchor = by_id[first_id]
        second_anchor = by_id[second_id]

        metric_x = (
            second_opening.offset_horizontal + second_opening.width / 2.0
            - first_opening.offset_horizontal - first_opening.width / 2.0
        )
        lego_x = (
            second_anchor.anchored_x_studs + second_anchor.anchored_width_studs / 2.0
            - first_anchor.anchored_x_studs - first_anchor.anchored_width_studs / 2.0
        )
        if metric_x > 0 and lego_x <= 0:
            return False
        if metric_x < 0 and lego_x >= 0:
            return False

        metric_z = (
            second_opening.offset_vertical + second_opening.height / 2.0
            - first_opening.offset_vertical - first_opening.height / 2.0
        )
        lego_z = (
            second_anchor.anchored_z_bricks + second_anchor.anchored_height_bricks / 2.0
            - first_anchor.anchored_z_bricks - first_anchor.anchored_height_bricks / 2.0
        )
        if metric_z > 0 and lego_z < 0:
            return False
        if metric_z < 0 and lego_z > 0:
            return False
    return True


def apply_opening_representation_plan(
    building: BuildingModel,
    shell: BuildingBrickShell,
    plan: LEGORepresentationPlan,
) -> OpeningPlanApplication:
    if plan.building_id != building.id or plan.volume_id != shell.volume_id:
        raise ValueError("opening representation plan does not match building/shell")

    openings = {
        item.id: item
        for item in building.openings
        if item.volume_id == shell.volume_id
    }
    reserved = {
        item.opening_id: item
        for item in plan.openings
        if item.status == "reserved"
    }
    updated_walls = []
    applied: list[AppliedOpeningAnchor] = []
    adjustments: list[OpeningRepresentationAdjustment] = []
    rejected: list[Facade] = []
    rejections: list[OpeningPlanRejection] = []

    for wall in shell.walls:
        wall_reservations = {
            raster.id: reserved[raster.id]
            for raster in wall.grid.openings
            if raster.id in reserved
        }
        if not wall_reservations:
            updated_walls.append(wall)
            continue

        opening_ids = sorted(wall_reservations)
        if not _identity_is_preserved(wall, openings, wall_reservations):
            rejected.append(wall.facade)
            rejections.append(_rejection(
                facade=wall.facade,
                code="architectural_identity_mismatch",
                opening_ids=opening_ids,
                reason=(
                    "reserved LEGO opening identity, facade, or semantic type does not match "
                    "the architectural opening; the facade remains unchanged"
                ),
            ))
            updated_walls.append(wall)
            continue

        vertical_records: list[tuple[object, WallOpeningGrid, int]] = []
        for raster in wall.grid.openings:
            reservation = wall_reservations.get(raster.id)
            opening = openings.get(raster.id)
            if reservation is None or opening is None:
                continue
            assert reservation.height_bricks is not None
            vertical_records.append((opening, raster, reservation.height_bricks))

        joint_z = _select_joint_z_starts(
            records=vertical_records,
            courses_per_meter=wall.grid.courses_per_meter,
            wall_height_bricks=wall.grid.height_bricks,
        )
        if joint_z is None:
            rejected.append(wall.facade)
            rejections.append(_rejection(
                facade=wall.facade,
                code="vertical_anchor_unsatisfied",
                opening_ids=opening_ids,
                reason="no facade-wide vertical anchor solution preserves the architectural level order",
            ))
            updated_walls.append(wall)
            continue

        joint_records: list[tuple[object, WallOpeningGrid, int, int, int]] = []
        for raster in wall.grid.openings:
            reservation = wall_reservations.get(raster.id)
            opening = openings.get(raster.id)
            if reservation is None or opening is None:
                continue
            assert reservation.width_studs is not None
            assert reservation.height_bricks is not None
            joint_records.append((
                opening,
                raster,
                reservation.width_studs,
                reservation.height_bricks,
                joint_z[opening.id],
            ))

        joint_x = _select_joint_x_starts(
            records=joint_records,
            studs_per_meter=wall.grid.studs_per_meter,
            wall_width_studs=wall.grid.width_studs,
        )
        if joint_x is None:
            rejected.append(wall.facade)
            rejections.append(_rejection(
                facade=wall.facade,
                code="horizontal_anchor_unsatisfied",
                opening_ids=opening_ids,
                reason="no facade-wide horizontal anchor solution preserves opening order and spacing",
            ))
            updated_walls.append(wall)
            continue

        proposed: list[WallOpeningGrid] = []
        facade_anchors: list[AppliedOpeningAnchor] = []
        for raster in wall.grid.openings:
            reservation = wall_reservations.get(raster.id)
            opening = openings.get(raster.id)
            if reservation is None or opening is None:
                proposed.append(raster)
                continue
            assert reservation.representation_role is not None
            assert reservation.motif_id is not None
            assert reservation.assembly_id is not None
            assert reservation.width_studs is not None
            assert reservation.height_bricks is not None
            x = joint_x[opening.id]
            z = joint_z[opening.id]
            proposed.append(raster.model_copy(update={
                "x_studs": x,
                "z_bricks": z,
                "width_studs": reservation.width_studs,
                "height_bricks": reservation.height_bricks,
            }))
            facade_anchors.append(AppliedOpeningAnchor(
                opening_id=opening.id,
                facade=wall.facade,
                representation_role=reservation.representation_role,
                motif_id=reservation.motif_id,
                assembly_id=reservation.assembly_id,
                source_x_studs=raster.x_studs,
                source_z_bricks=raster.z_bricks,
                source_width_studs=raster.width_studs,
                source_height_bricks=raster.height_bricks,
                anchored_x_studs=x,
                anchored_z_bricks=z,
                anchored_width_studs=reservation.width_studs,
                anchored_height_bricks=reservation.height_bricks,
            ))

        if not _architectural_order_is_preserved(facade_anchors, openings):
            rejected.append(wall.facade)
            rejections.append(_rejection(
                facade=wall.facade,
                code="architectural_order_not_preserved",
                opening_ids=opening_ids,
                reason="proposed LEGO anchors invert or collapse known architectural opening order",
            ))
            updated_walls.append(wall)
            continue

        facade_adjustments = [
            OpeningRepresentationAdjustment.from_anchor(anchor)
            for anchor in facade_anchors
        ]
        if any(not item.within_local_bounds for item in facade_adjustments):
            rejected.append(wall.facade)
            rejections.append(_rejection(
                facade=wall.facade,
                code="adjustment_exceeds_local_bound",
                opening_ids=opening_ids,
                reason=(
                    "proposed LEGO opening translation or footprint delta exceeds the explicit "
                    "one-unit local representation envelope"
                ),
            ))
            updated_walls.append(wall)
            continue

        try:
            layout = generate_wall_layout_with_openings(
                width_studs=wall.grid.width_studs,
                height_bricks=wall.grid.height_bricks,
                openings=proposed,
            )
        except ValueError:
            rejected.append(wall.facade)
            rejections.append(_rejection(
                facade=wall.facade,
                code="facade_layout_invalid",
                opening_ids=opening_ids,
                reason="proposed facade opening reservations overlap or exceed the validated wall layout",
            ))
            updated_walls.append(wall)
            continue

        grid = wall.grid.model_copy(update={"openings": proposed})
        updated_walls.append(wall.model_copy(update={"grid": grid, "layout": layout}))
        applied.extend(facade_anchors)
        adjustments.extend(facade_adjustments)

    return OpeningPlanApplication(
        shell=shell.model_copy(update={"walls": updated_walls}),
        anchors=applied,
        adjustments=adjustments,
        rejected_facades=rejected,
        rejections=rejections,
    )
