"""Packaging contract derived from AssemblyPlan without changing construction order."""
from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field, model_validator

from .assembly import AssemblyPlan


class BagGroup(BaseModel):
    bag_number: int = Field(gt=0)
    phases: list[str] = Field(min_length=1)
    assembly_step_ids: list[str] = Field(min_length=1)
    placement_ids: list[str] = Field(min_length=1)


class BagPlan(BaseModel):
    schema_version: str = "0.1"
    building_id: str
    volume_id: str
    total_bags: int = Field(gt=0)
    total_parts: int = Field(gt=0)
    bags: list[BagGroup] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_structure(self) -> "BagPlan":
        numbers = [bag.bag_number for bag in self.bags]
        if numbers != list(range(1, self.total_bags + 1)):
            raise ValueError("bag plan numbers must be contiguous from 1")
        step_ids = [step_id for bag in self.bags for step_id in bag.assembly_step_ids]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("bag plan assembly step ids must be unique")
        placement_ids = [placement_id for bag in self.bags for placement_id in bag.placement_ids]
        if len(placement_ids) != len(set(placement_ids)):
            raise ValueError("bag plan placement ids must be unique")
        if self.total_parts != len(placement_ids):
            raise ValueError("total_parts does not match bag placement count")
        return self


def generate_bag_plan(assembly_plan: AssemblyPlan) -> BagPlan:
    """Project existing deterministic bag assignments into a standalone contract.

    The first version intentionally preserves AssemblyPlan's current phase-based
    grouping. It creates a migration seam so later packing optimization can split
    or regroup bags without changing construction order or InstructionPlan.
    """
    by_bag = defaultdict(list)
    for step in assembly_plan.steps:
        by_bag[step.bag].append(step)

    bags: list[BagGroup] = []
    for bag_number in sorted(by_bag):
        steps = sorted(by_bag[bag_number], key=lambda step: step.sequence)
        phases = list(dict.fromkeys(step.phase for step in steps))
        bags.append(BagGroup(
            bag_number=bag_number,
            phases=phases,
            assembly_step_ids=[step.step_id for step in steps],
            placement_ids=[placement_id for step in steps for placement_id in step.placement_ids],
        ))

    return BagPlan(
        building_id=assembly_plan.building_id,
        volume_id=assembly_plan.volume_id,
        total_bags=len(bags),
        total_parts=assembly_plan.total_parts,
        bags=bags,
    )
