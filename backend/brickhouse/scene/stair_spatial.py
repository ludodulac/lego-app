"""Conservative spatial facts for architectural stair runs.

A StairRun gives a start point, end point and width, but no tread thickness or
solid body profile. This module therefore derives a 2D corridor plus a vertical
span and endpoint contacts. It deliberately does not turn that information into
a filled 3D prism.
"""
from __future__ import annotations

from math import hypot
from typing import Literal

from pydantic import BaseModel, Field

from .models import CONNECTIVITY_TOLERANCE_M, EPSILON, Platform, SceneVolume, StairRun


class StairCorridor(BaseModel):
    stair_id: str
    geometry_known: bool
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None
    z_min: float | None = None
    z_max: float | None = None
    horizontal_run: float | None = Field(default=None, ge=0)
    width: float | None = Field(default=None, gt=0)
    solid_volume_known: bool = False


StairEndpoint = Literal["start", "end"]
StairContactKind = Literal["platform_top", "volume_boundary"]


class StairEndpointContact(BaseModel):
    stair_id: str
    endpoint: StairEndpoint
    target_id: str
    contact_kind: StairContactKind


class StairSpatialReport(BaseModel):
    corridors: list[StairCorridor]
    endpoint_contacts: list[StairEndpointContact]

    def corridor(self, stair_id: str) -> StairCorridor | None:
        return next((item for item in self.corridors if item.stair_id == stair_id), None)

    def contacts(self, stair_id: str, endpoint: StairEndpoint | None = None) -> list[StairEndpointContact]:
        return [
            item
            for item in self.endpoint_contacts
            if item.stair_id == stair_id and (endpoint is None or item.endpoint == endpoint)
        ]


def _corridor(stair: StairRun) -> StairCorridor:
    dx = stair.end.x - stair.start.x
    dy = stair.end.y - stair.start.y
    run = hypot(dx, dy)
    z_min = min(stair.start.z, stair.end.z)
    z_max = max(stair.start.z, stair.end.z)
    if run <= EPSILON:
        return StairCorridor(
            stair_id=stair.id,
            geometry_known=False,
            z_min=z_min,
            z_max=z_max,
            horizontal_run=run,
            width=stair.width,
        )

    # Offset the centerline by half the stair width along its XY perpendicular.
    # The axis-aligned bounds conservatively contain the exact corridor polygon.
    half = stair.width / 2.0
    px = -dy / run * half
    py = dx / run * half
    points = (
        (stair.start.x + px, stair.start.y + py),
        (stair.start.x - px, stair.start.y - py),
        (stair.end.x + px, stair.end.y + py),
        (stair.end.x - px, stair.end.y - py),
    )
    return StairCorridor(
        stair_id=stair.id,
        geometry_known=True,
        x_min=min(point[0] for point in points),
        x_max=max(point[0] for point in points),
        y_min=min(point[1] for point in points),
        y_max=max(point[1] for point in points),
        z_min=z_min,
        z_max=z_max,
        horizontal_run=run,
        width=stair.width,
        solid_volume_known=False,
    )


def _point_on_platform_top(point, platform: Platform) -> bool:
    return (
        platform.position.x - CONNECTIVITY_TOLERANCE_M <= point.x <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
        and platform.position.y - CONNECTIVITY_TOLERANCE_M <= point.y <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
        and abs(point.z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
    )


def _volume_bounds(volume: SceneVolume):
    values = (volume.width.value, volume.depth.value, volume.height.value)
    if any(value is None for value in values):
        return None
    width, depth, height = values
    assert width is not None and depth is not None and height is not None
    return (
        volume.position.x,
        volume.position.x + width,
        volume.position.y,
        volume.position.y + depth,
        volume.position.z,
        volume.position.z + height,
    )


def _point_on_volume_boundary(point, volume: SceneVolume) -> bool:
    bounds = _volume_bounds(volume)
    if bounds is None:
        return False
    x0, x1, y0, y1, z0, z1 = bounds
    inside_x = x0 - CONNECTIVITY_TOLERANCE_M <= point.x <= x1 + CONNECTIVITY_TOLERANCE_M
    inside_y = y0 - CONNECTIVITY_TOLERANCE_M <= point.y <= y1 + CONNECTIVITY_TOLERANCE_M
    inside_z = z0 - CONNECTIVITY_TOLERANCE_M <= point.z <= z1 + CONNECTIVITY_TOLERANCE_M
    if not (inside_x and inside_y and inside_z):
        return False
    return (
        min(abs(point.x - x0), abs(point.x - x1)) <= CONNECTIVITY_TOLERANCE_M
        or min(abs(point.y - y0), abs(point.y - y1)) <= CONNECTIVITY_TOLERANCE_M
        or min(abs(point.z - z0), abs(point.z - z1)) <= CONNECTIVITY_TOLERANCE_M
    )


def analyze_stair_spatial(scene) -> StairSpatialReport:
    corridors = [_corridor(stair) for stair in sorted(scene.stairs, key=lambda item: item.id)]
    contacts: list[StairEndpointContact] = []
    for stair in sorted(scene.stairs, key=lambda item: item.id):
        for endpoint_name, point in (("start", stair.start), ("end", stair.end)):
            for platform in sorted(scene.platforms, key=lambda item: item.id):
                if _point_on_platform_top(point, platform):
                    contacts.append(
                        StairEndpointContact(
                            stair_id=stair.id,
                            endpoint=endpoint_name,
                            target_id=platform.id,
                            contact_kind="platform_top",
                        )
                    )
            for volume in sorted(scene.volumes, key=lambda item: item.id):
                if _point_on_volume_boundary(point, volume):
                    contacts.append(
                        StairEndpointContact(
                            stair_id=stair.id,
                            endpoint=endpoint_name,
                            target_id=volume.id,
                            contact_kind="volume_boundary",
                        )
                    )
    contacts.sort(key=lambda item: (item.stair_id, item.endpoint, item.target_id, item.contact_kind))
    return StairSpatialReport(corridors=corridors, endpoint_contacts=contacts)
