"""Canonical endpoint-contact semantics for metric Scene stair runs.

A StairRun is a centerline-like metric primitive, not a filled stair solid. Two
runs therefore connect only through their explicit endpoints. Corridor overlap,
parallel proximity, or inferred landings are deliberately not treated as contact.
"""
from __future__ import annotations

from math import hypot
from typing import Literal

from pydantic import BaseModel, Field

from .models import CONNECTIVITY_TOLERANCE_M


StairEndpointName = Literal["start", "end"]


class StairRunEndpointContact(BaseModel):
    first_run_id: str
    second_run_id: str
    first_endpoint: StairEndpointName
    second_endpoint: StairEndpointName
    horizontal_gap: float = Field(ge=0)
    vertical_gap: float = Field(ge=0)


def closest_stair_run_endpoint_contact(first, second) -> StairRunEndpointContact | None:
    """Return the closest endpoint pair when it satisfies canonical contact tolerance."""
    best = None
    for first_name, first_point in (("start", first.start), ("end", first.end)):
        for second_name, second_point in (("start", second.start), ("end", second.end)):
            horizontal_gap = hypot(first_point.x - second_point.x, first_point.y - second_point.y)
            vertical_gap = abs(first_point.z - second_point.z)
            key = (max(horizontal_gap, vertical_gap), horizontal_gap + vertical_gap)
            if best is None or key < best[0]:
                best = (key, first_name, second_name, horizontal_gap, vertical_gap)

    assert best is not None
    _, first_name, second_name, horizontal_gap, vertical_gap = best
    if horizontal_gap > CONNECTIVITY_TOLERANCE_M or vertical_gap > CONNECTIVITY_TOLERANCE_M:
        return None
    return StairRunEndpointContact(
        first_run_id=first.id,
        second_run_id=second.id,
        first_endpoint=first_name,
        second_endpoint=second_name,
        horizontal_gap=horizontal_gap,
        vertical_gap=vertical_gap,
    )


def stair_runs_touch_at_endpoints(first, second) -> bool:
    return closest_stair_run_endpoint_contact(first, second) is not None


def stair_endpoint_touches_run(point, other) -> bool:
    """Return whether one explicit endpoint touches either endpoint of another run."""
    for other_point in (other.start, other.end):
        horizontal_gap = hypot(point.x - other_point.x, point.y - other_point.y)
        vertical_gap = abs(point.z - other_point.z)
        if horizontal_gap <= CONNECTIVITY_TOLERANCE_M and vertical_gap <= CONNECTIVITY_TOLERANCE_M:
            return True
    return False
