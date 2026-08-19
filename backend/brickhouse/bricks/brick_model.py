"""Canonical supplier-independent BrickModel for downstream consumers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import Facade, RidgeDirection

from .facade_details import FacadeDetailPlacement
from .roof import SUPPORTED_SLOPE_FAMILIES, SpatialRoof, create_m0_roof_catalog
from .spatial import SpatialBrickShell

PartCategory = Literal["brick", "roof_tile", "ridge_tile", "window_frame", "window_pane", "facade_detail"]
PartComponent = Literal["wall", "roof", "facade_detail"]


class BrickModelPart(BaseModel):
    placement_id: str
    part_id: str
    category: PartCategory
    component: PartComponent
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]
    facade: Facade | None = None
    roof_side: Literal["negative", "positive", "ridge"] | None = None

    @model_validator(mode="after")
    def validate_semantic_zone(self) -> "BrickModelPart":
        if self.component == "wall":
            if self.facade is None or self.roof_side is not None:
                raise ValueError("wall parts require facade and must not define roof_side")
            if self.category != "brick":
                raise ValueError("wall parts must use category 'brick'")
        elif self.component == "roof":
            if self.roof_side is None or self.facade is not None:
                raise ValueError("roof parts require roof_side and must not define facade")
            expected = "ridge_tile" if self.roof_side == "ridge" else "roof_tile"
            if self.category != expected:
                raise ValueError(f"roof part on side {self.roof_side!r} must use category {expected!r}")
        else:
            if self.facade is None or self.roof_side is not None:
                raise ValueError("facade detail parts require facade and must not define roof_side")
            if self.category not in {"brick", "window_frame", "window_pane", "facade_detail"}:
                raise ValueError("facade detail parts must use a facade-compatible category")
        return self


class BrickModel(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    width_studs: int = Field(gt=0)
    depth_studs: int = Field(gt=0)
    height_plates: int = Field(gt=0)
    parts: list[BrickModelPart] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_placement_ids(self) -> "BrickModel":
        ids = [part.placement_id for part in self.parts]
        if len(ids) != len(set(ids)):
            raise ValueError("BrickModel placement IDs must be unique")
        return self


def _roof_category(part_id: str, side: str) -> Literal["roof_tile", "ridge_tile"]:
    try:
        definition = create_m0_roof_catalog().get(part_id)
    except KeyError as exc:
        raise ValueError(f"unknown canonical roof part {part_id!r}") from exc
    expected = "ridge_tile" if side == "ridge" else "roof_tile"
    if definition.category != expected:
        raise ValueError(f"roof placement {part_id!r} has category {definition.category!r}, expected {expected!r}")
    return expected


def _roof_family(roof: SpatialRoof):
    catalog = create_m0_roof_catalog()
    family_ids = {
        catalog.get(placement.part_id).slope_family
        for placement in roof.placements
        if placement.side in {"negative", "positive"}
    }
    family_ids.discard(None)
    if len(family_ids) != 1:
        raise ValueError("gable wall generation requires exactly one roof slope family")
    family_id = next(iter(family_ids))
    return next(family for family in SUPPORTED_SLOPE_FAMILIES if family.id == family_id)


def _generate_gable_wall_parts(shell: SpatialBrickShell, roof: SpatialRoof) -> list[BrickModelPart]:
    """Fill both gable ends with inset stepped brickwork following the roof family."""
    family = _roof_family(roof)
    wall_top = shell.height_bricks * 3
    negative = [placement for placement in roof.placements if placement.side == "negative"]
    if not negative:
        return []
    if roof.ridge_direction is RidgeDirection.DEPTH:
        slope_axes = {placement.x_studs for placement in negative}
        span = shell.width_studs
        facades = (Facade.FRONT, Facade.REAR)
    else:
        slope_axes = {placement.y_studs for placement in negative}
        span = shell.depth_studs
        facades = (Facade.LEFT, Facade.RIGHT)
    course_count = len(slope_axes)
    result: list[BrickModelPart] = []
    index = 1
    for facade in facades:
        for level in range(course_count):
            trim = 1 + level * family.course_advance_studs
            start = trim
            end = span - trim
            if end <= start:
                continue
            z_plates = wall_top + level * family.rise_plates
            for local in range(start, end):
                if roof.ridge_direction is RidgeDirection.DEPTH:
                    x = local
                    y = 1 if facade is Facade.FRONT else max(shell.depth_studs - 2, 0)
                else:
                    x = 1 if facade is Facade.LEFT else max(shell.width_studs - 2, 0)
                    y = local
                result.append(
                    BrickModelPart(
                        placement_id=f"gable-{index:06d}",
                        part_id="BRICK_1X1",
                        category="brick",
                        component="wall",
                        x_studs=x,
                        y_studs=y,
                        z_plates=z_plates,
                        rotation_quarter_turns=0,
                        facade=facade,
                    )
                )
                index += 1
    return result


def generate_brick_model(
    shell: SpatialBrickShell,
    roof: SpatialRoof,
    facade_details: list[FacadeDetailPlacement] | None = None,
) -> BrickModel:
    """Merge spatial walls, closed gable ends, facade details and roof into BrickModel."""
    if shell.building_id != roof.building_id:
        raise ValueError("spatial shell and roof must reference the same building")
    parts: list[BrickModelPart] = []
    for index, placement in enumerate(shell.placements, start=1):
        parts.append(BrickModelPart(placement_id=f"wall-{index:06d}", part_id=placement.brick_id, category="brick", component="wall", x_studs=placement.x_studs, y_studs=placement.y_studs, z_plates=placement.z_plates, rotation_quarter_turns=placement.rotation_quarter_turns, facade=placement.facade))
    parts.extend(_generate_gable_wall_parts(shell, roof))
    for index, placement in enumerate(facade_details or [], start=1):
        parts.append(BrickModelPart(placement_id=f"detail-{index:06d}", part_id=placement.part_id, category=placement.category, component="facade_detail", x_studs=placement.x_studs, y_studs=placement.y_studs, z_plates=placement.z_plates, rotation_quarter_turns=placement.rotation_quarter_turns, facade=placement.facade))
    for index, placement in enumerate(roof.placements, start=1):
        parts.append(BrickModelPart(placement_id=f"roof-{index:06d}", part_id=placement.part_id, category=_roof_category(placement.part_id, placement.side), component="roof", x_studs=placement.x_studs, y_studs=placement.y_studs, z_plates=placement.z_plates, rotation_quarter_turns=placement.rotation_quarter_turns, roof_side=placement.side))
    wall_top = shell.height_bricks * 3
    catalog = create_m0_roof_catalog()
    roof_top = max((p.z_plates + catalog.get(p.part_id).height_plates for p in roof.placements), default=wall_top)
    return BrickModel(building_id=shell.building_id, volume_id=shell.volume_id, width_studs=shell.width_studs, depth_studs=shell.depth_studs, height_plates=max(wall_top, roof_top), parts=parts)
