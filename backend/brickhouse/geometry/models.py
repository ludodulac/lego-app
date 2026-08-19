"""Deterministic geometric representation derived from BuildingModel v0.1."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade, OpeningType, RidgeDirection, RoofType


class Point3D(BaseModel):
    x: float
    y: float
    z: float


class OpeningGeometry(BaseModel):
    id: str
    opening_type: OpeningType
    volume_id: str
    facade: Facade
    corners: list[Point3D] = Field(min_length=4, max_length=4)


class WallGeometry(BaseModel):
    id: str
    volume_id: str
    facade: Facade
    corners: list[Point3D] = Field(min_length=4, max_length=4)
    openings: list[OpeningGeometry] = Field(default_factory=list)


class RoofPlaneGeometry(BaseModel):
    id: str
    roof_id: str
    volume_id: str
    roof_type: RoofType
    side: Literal["flat", "negative", "positive"]
    ridge_direction: RidgeDirection | None = None
    corners: list[Point3D] = Field(min_length=4, max_length=4)


class BuildingGeometry(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    units: Literal["m"] = "m"
    walls: list[WallGeometry]
    roof_planes: list[RoofPlaneGeometry]
