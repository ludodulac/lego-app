"""Serializable progressive-build state shared by preview and future instructions."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .assembly import AssemblyPlan
from .brick_model import BrickModel, BrickModelPart


class BuildPreviewState(BaseModel):
    """Exact BrickModel subset visible after a selected assembly step."""

    building_id: str
    volume_id: str
    selected_step: int = Field(ge=0)
    total_steps: int = Field(gt=0)
    visible_parts: list[BrickModelPart]
    current_placement_ids: list[str]
    current_title: str | None = None
    current_phase: str | None = None


def build_preview_state(
    model: BrickModel,
    plan: AssemblyPlan,
    selected_step: int,
) -> BuildPreviewState:
    """Return the exact cumulative part set for ``selected_step``.

    The preview is deliberately incapable of inventing geometry: every visible
    part is looked up by placement ID in the canonical BrickModel, and the
    selected step must belong to the AssemblyPlan generated for that model.
    """
    if model.building_id != plan.building_id or model.volume_id != plan.volume_id:
        raise ValueError("BrickModel and AssemblyPlan must reference the same build")
    if selected_step < 0 or selected_step > plan.total_steps:
        raise ValueError(f"selected_step must be between 0 and {plan.total_steps}")

    parts_by_id = {part.placement_id: part for part in model.parts}
    planned_ids = [pid for step in plan.steps for pid in step.placement_ids]
    if set(planned_ids) != set(parts_by_id) or len(planned_ids) != len(parts_by_id):
        raise ValueError("AssemblyPlan must reference every BrickModel placement exactly once")

    if selected_step == 0:
        return BuildPreviewState(
            building_id=model.building_id,
            volume_id=model.volume_id,
            selected_step=0,
            total_steps=plan.total_steps,
            visible_parts=[],
            current_placement_ids=[],
        )

    selected = plan.steps[selected_step - 1]
    visible_ids = {
        pid
        for step in plan.steps[:selected_step]
        for pid in step.placement_ids
    }
    # Preserve canonical BrickModel ordering for deterministic rendering/export.
    visible_parts = [part for part in model.parts if part.placement_id in visible_ids]

    return BuildPreviewState(
        building_id=model.building_id,
        volume_id=model.volume_id,
        selected_step=selected_step,
        total_steps=plan.total_steps,
        visible_parts=visible_parts,
        current_placement_ids=list(selected.placement_ids),
        current_title=selected.title,
        current_phase=selected.phase,
    )
