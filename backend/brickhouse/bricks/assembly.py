"""Deterministic M0 assembly ordering derived from BrickModel."""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field, model_validator

from .brick_model import BrickModel, PartComponent


class AssemblyStep(BaseModel):
    step_id: str
    sequence: int = Field(gt=0)
    component: PartComponent
    z_plates: int = Field(ge=0)
    title: str
    placement_ids: list[str] = Field(min_length=1)


class AssemblyPlan(BaseModel):
    schema_version: str = "0.1"
    building_id: str
    volume_id: str
    total_steps: int = Field(gt=0)
    total_parts: int = Field(gt=0)
    steps: list[AssemblyStep] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_structure(self) -> "AssemblyPlan":
        if self.total_steps != len(self.steps):
            raise ValueError("total_steps does not match steps length")
        if [step.sequence for step in self.steps] != list(range(1, len(self.steps) + 1)):
            raise ValueError("assembly step sequences must be contiguous from 1")
        ids = [placement_id for step in self.steps for placement_id in step.placement_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("assembly plan placement ids must be unique")
        if self.total_parts != len(ids):
            raise ValueError("total_parts does not match referenced placement count")
        return self


def _phase_for_part(part) -> str:
    if part.component == "wall":
        return "wall"
    if part.component == "roof":
        return "roof"
    if part.category == "window_frame":
        return "window_frame"
    if part.category == "window_pane":
        return "window_pane"
    return "facade_detail"


def generate_assembly_plan(model: BrickModel) -> AssemblyPlan:
    """Generate a bottom-up plan with physically sensible window sequencing.

    Real window frames are placed before their panes. Other facade details remain
    separate, so the printable instructions never ask the builder to insert a
    pane before the supporting frame exists.
    """
    groups: dict[tuple[str, int], list[str]] = defaultdict(list)
    for part in model.parts:
        groups[(_phase_for_part(part), part.z_plates)].append(part.placement_id)

    ordered_groups: list[tuple[str, int]] = []
    for phase in ("wall", "window_frame", "window_pane", "facade_detail", "roof"):
        z_values = sorted(z for (kind, z) in groups if kind == phase)
        ordered_groups.extend((phase, z) for z in z_values)

    labels = {
        "wall": "Murs",
        "window_frame": "Cadres de fenêtres",
        "window_pane": "Vitrages",
        "facade_detail": "Détails de façade",
        "roof": "Toiture",
    }
    components: dict[str, PartComponent] = {
        "wall": "wall",
        "window_frame": "facade_detail",
        "window_pane": "facade_detail",
        "facade_detail": "facade_detail",
        "roof": "roof",
    }
    steps: list[AssemblyStep] = []
    for sequence, (phase, z_plates) in enumerate(ordered_groups, start=1):
        placement_ids = sorted(groups[(phase, z_plates)])
        steps.append(
            AssemblyStep(
                step_id=f"step-{sequence:04d}",
                sequence=sequence,
                component=components[phase],
                z_plates=z_plates,
                title=f"{labels[phase]} — niveau {z_plates} plates",
                placement_ids=placement_ids,
            )
        )

    all_model_ids = {part.placement_id for part in model.parts}
    all_plan_ids = {placement_id for step in steps for placement_id in step.placement_ids}
    if all_plan_ids != all_model_ids:
        missing = sorted(all_model_ids - all_plan_ids)
        extra = sorted(all_plan_ids - all_model_ids)
        raise RuntimeError(f"assembly coverage mismatch: missing={missing!r}, extra={extra!r}")

    return AssemblyPlan(
        building_id=model.building_id,
        volume_id=model.volume_id,
        total_steps=len(steps),
        total_parts=len(model.parts),
        steps=steps,
    )
