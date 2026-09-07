"""Apply LEGORepresentationPlan opening reservations to the derived wall grid.

This is a representation-only mutation. Architectural opening metrics and semantic
types remain untouched; only the downstream LEGO wall voids are locally anchored
to the exact curated motif footprints selected by the plan.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade

from .building_layout import BuildingBrickShell
from .opening_representation_plan import LEGORepresentationPlan, OpeningRepresentationRole
from .placement import WallOpeningGrid, generate_wall_layout_with_openings
from .window_anchors import _select_joint_x_starts, _select_joint_z_starts


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


class OpeningPlanApplication(BaseModel):
    shell: BuildingBrickShell
    anchors: list[AppliedOpeningAnchor] = Field(default_factory=list)
    rejected_facades: list[Facade] = Field(default_factory=list)


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
    rejected: list[Facade] = []

    for wall in shell.walls:
        wall_reservations = {
            raster.id: reserved[raster.id]
            for raster in wall.grid.openings
            if raster.id in reserved
        }
        if not wall_reservations:
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

        try:
            layout = generate_wall_layout_with_openings(
                width_studs=wall.grid.width_studs,
                height_bricks=wall.grid.height_bricks,
                openings=proposed,
            )
        except ValueError:
            rejected.append(wall.facade)
            updated_walls.append(wall)
            continue

        grid = wall.grid.model_copy(update={"openings": proposed})
        updated_walls.append(wall.model_copy(update={"grid": grid, "layout": layout}))
        applied.extend(facade_anchors)

    return OpeningPlanApplication(
        shell=shell.model_copy(update={"walls": updated_walls}),
        anchors=applied,
        rejected_facades=rejected,
    )
