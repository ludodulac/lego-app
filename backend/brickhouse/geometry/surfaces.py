"""Extensible architectural surface representation for BrickHouse.

The current deterministic M0 geometry is intentionally conservative and mostly
rectilinear.  This module provides a second, supplier-independent surface layer
that can represent the same ordinary buildings today without making four
cardinal facades or rectangular roof planes a permanent architectural
assumption.

Future vision/Scene reconstruction may emit these surfaces directly (including
polygonal, triangulated or curved envelopes) before any LEGO quantization.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import Facade

from .models import BuildingGeometry, Point3D


class ArchitecturalSurfaceKind(str, Enum):
    PLANAR_POLYGON = "planar_polygon"
    TRIANGULATED_MESH = "triangulated_mesh"
    CURVED_PATCH = "curved_patch"


class ArchitecturalSurfaceRole(str, Enum):
    WALL = "wall"
    ROOF = "roof"
    GLAZING = "glazing"
    SOFFIT = "soffit"
    FLOOR = "floor"
    EXTERIOR_STRUCTURE = "exterior_structure"
    ENVELOPE = "envelope"
    OTHER = "other"


class SurfaceTriangle(BaseModel):
    """Triangle indices into ``ArchitecturalSurface.vertices``."""

    a: int = Field(ge=0)
    b: int = Field(ge=0)
    c: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_distinct_vertices(self):
        if len({self.a, self.b, self.c}) != 3:
            raise ValueError("surface triangle must reference three distinct vertices")
        return self


class ArchitecturalSurface(BaseModel):
    id: str
    role: ArchitecturalSurfaceRole
    kind: ArchitecturalSurfaceKind
    vertices: list[Point3D] = Field(min_length=3)
    triangles: list[SurfaceTriangle] = Field(default_factory=list)
    source_object_ids: list[str] = Field(default_factory=list)
    facade_hint: Facade | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_topology(self):
        if self.kind is ArchitecturalSurfaceKind.PLANAR_POLYGON and self.triangles:
            raise ValueError("planar polygon surfaces do not require explicit triangles")
        if self.kind is ArchitecturalSurfaceKind.TRIANGULATED_MESH:
            if not self.triangles:
                raise ValueError("triangulated mesh surfaces require triangles")
            limit = len(self.vertices)
            if any(max(t.a, t.b, t.c) >= limit for t in self.triangles):
                raise ValueError("surface triangle references a vertex outside the vertex list")
        return self


class ArchitecturalSurfaceModel(BaseModel):
    """Geometry before LEGO-specific discretization.

    ``0.1`` deliberately supports more surface kinds than the current M0 brick
    backend. Unsupported surfaces must remain explicit rather than being silently
    coerced into rectangular walls or a gable roof.
    """

    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    units: Literal["m"] = "m"
    surfaces: list[ArchitecturalSurface] = Field(default_factory=list)


def surface_model_from_building_geometry(geometry: BuildingGeometry) -> ArchitecturalSurfaceModel:
    """Losslessly lift today's planar M0 geometry into the generic surface layer."""
    surfaces: list[ArchitecturalSurface] = []
    for wall in geometry.walls:
        surfaces.append(
            ArchitecturalSurface(
                id=f"surface:{wall.id}",
                role=ArchitecturalSurfaceRole.WALL,
                kind=ArchitecturalSurfaceKind.PLANAR_POLYGON,
                vertices=wall.corners,
                source_object_ids=[wall.id],
                facade_hint=wall.facade,
                confidence=1.0,
            )
        )
        for opening in wall.openings:
            surfaces.append(
                ArchitecturalSurface(
                    id=f"surface:opening:{opening.id}",
                    role=ArchitecturalSurfaceRole.GLAZING,
                    kind=ArchitecturalSurfaceKind.PLANAR_POLYGON,
                    vertices=opening.corners,
                    source_object_ids=[opening.id, wall.id],
                    facade_hint=opening.facade,
                    confidence=1.0,
                    notes="Opening plane; semantic opening type remains in BuildingGeometry.",
                )
            )
    for roof in geometry.roof_planes:
        surfaces.append(
            ArchitecturalSurface(
                id=f"surface:{roof.id}",
                role=ArchitecturalSurfaceRole.ROOF,
                kind=ArchitecturalSurfaceKind.PLANAR_POLYGON,
                vertices=roof.corners,
                source_object_ids=[roof.id, roof.roof_id],
                confidence=1.0,
            )
        )
    return ArchitecturalSurfaceModel(building_id=geometry.building_id, surfaces=surfaces)
