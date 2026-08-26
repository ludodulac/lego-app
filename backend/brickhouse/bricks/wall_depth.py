"""Project resolved facade wall/reveal depth into conservative LEGO geometry."""
from __future__ import annotations

from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene

from .brick_model import BrickModel, BrickModelPart
from .catalog import create_m0_brick_catalog

MIN_GEOMETRY_CONFIDENCE = 0.65


def _resolved_metric(property_value) -> float | None:
    if property_value is None or property_value.value is None:
        return None
    source = property_value.source
    if source.kind == "user_provided" or source.confidence >= MIN_GEOMETRY_CONFIDENCE:
        return property_value.value
    return None


def _shift_inward(part: BrickModelPart, facade: Facade, depth_studs: int) -> dict[str, int]:
    if facade is Facade.FRONT:
        return {"y_studs": part.y_studs + depth_studs}
    if facade is Facade.REAR:
        return {"y_studs": part.y_studs - depth_studs}
    if facade is Facade.LEFT:
        return {"x_studs": part.x_studs + depth_studs}
    return {"x_studs": part.x_studs - depth_studs}


def _within_model(model: BrickModel, part: BrickModelPart) -> bool:
    return 0 <= part.x_studs < model.width_studs and 0 <= part.y_studs < model.depth_studs


def _wall_cells(part: BrickModelPart) -> set[tuple[int, int, int]]:
    if part.component != "wall" or part.category != "brick":
        return set()
    brick = create_m0_brick_catalog().get(part.part_id)
    width, depth = brick.footprint(part.rotation_quarter_turns)
    return {
        (part.x_studs + dx, part.y_studs + dy, part.z_plates)
        for dx in range(width)
        for dy in range(depth)
    }


def augment_brick_model_with_wall_depth(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Thicken resolved facade walls and recess glazing without guessing unknown depth.

    This first construction slice deliberately supports a single modeled volume.
    It duplicates the already-rasterized exterior wall courses inward, so opening
    cuts remain clear through every added wall layer. Numeric wall/reveal values
    are used only when user-provided or sufficiently confident; an observation
    that merely says "recessed" never invents a LEGO depth.
    """
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    if len(scene.volumes) != 1 or model.volume_id == "composite":
        return model
    primary_width = scene.volumes[0].width.value
    if primary_width is None or primary_width <= 0:
        return model
    studs_per_meter = front_width_studs / primary_width
    profiles = [
        profile
        for profile in getattr(scene, "wall_profile_observations", [])
        if profile.volume_id == scene.volumes[0].id
    ]
    if not profiles:
        return model

    parts = list(model.parts)
    changed = False
    occupied = set().union(*(_wall_cells(part) for part in parts)) if parts else set()
    additions: list[BrickModelPart] = []

    for profile in profiles:
        thickness_m = _resolved_metric(profile.wall_thickness)
        thickness_studs = max(1, round(thickness_m * studs_per_meter)) if thickness_m is not None else 1
        source_wall_parts = [
            part
            for part in model.parts
            if part.component == "wall" and part.facade is profile.facade
        ]
        for layer in range(1, thickness_studs):
            for part in source_wall_parts:
                candidate = part.model_copy(update={
                    "placement_id": f"wall-depth:{profile.id}:{layer}:{part.placement_id}",
                    **_shift_inward(part, profile.facade, layer),
                })
                if not _within_model(model, candidate):
                    continue
                cells = _wall_cells(candidate)
                if cells & occupied:
                    continue
                occupied.update(cells)
                additions.append(candidate)
                changed = True

        reveal_m = _resolved_metric(profile.reveal_depth)
        if reveal_m is None:
            continue
        reveal_studs = max(0, round(reveal_m * studs_per_meter))
        if thickness_m is not None:
            reveal_studs = min(reveal_studs, max(0, thickness_studs - 1))
        if reveal_studs <= 0:
            continue
        for index, part in enumerate(parts):
            if part.facade is not profile.facade or part.category not in {"window_frame", "window_pane"}:
                continue
            moved = part.model_copy(update=_shift_inward(part, profile.facade, reveal_studs))
            if _within_model(model, moved):
                parts[index] = moved
                changed = True

    if not changed:
        return model
    return model.model_copy(update={"parts": [*parts, *additions]})
