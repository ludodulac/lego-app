"""Deterministic pre-build summary derived from the real BrickHouse pipeline.

This is intentionally not a wall-area heuristic. The estimator runs the same
catalog/layout pipeline as construction and returns only a lightweight summary,
so the user can see the current part count before committing to the build flow.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from brickhouse.pipeline import run_m0_pipeline_model


class BuildPartEstimate(BaseModel):
    requested_front_width_studs: int = Field(gt=0)
    part_count_min: int = Field(ge=0)
    part_count_max: int = Field(ge=0)
    estimated_parts: int = Field(ge=0)
    unique_part_types: int = Field(ge=0)
    basis: Literal["deterministic_dry_run"] = "deterministic_dry_run"


def estimate_build_parts(
    building: BuildingModel,
    *,
    front_width_studs: int,
) -> BuildPartEstimate:
    """Return an exact current-engine estimate without inventing a heuristic band.

    The response is shaped as a min/max band for forward compatibility. Because
    the current M0 pipeline is deterministic for a fixed input and target width,
    both bounds are deliberately equal to the dry-run BOM total.
    """
    bundle = run_m0_pipeline_model(
        building,
        front_width_studs=front_width_studs,
    )
    total = bundle.bom.total_parts
    return BuildPartEstimate(
        requested_front_width_studs=front_width_studs,
        part_count_min=total,
        part_count_max=total,
        estimated_parts=total,
        unique_part_types=bundle.bom.unique_part_types,
    )
