"""Apply Scene material semantics to rich BrickModel exterior parts."""
from __future__ import annotations

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel
from .scene_architecture import _is_timber


def apply_scene_part_categories(model: BrickModel, scene: ArchitecturalScene) -> BrickModel:
    """Reclassify generated exterior parts for viewer/BOM material distinction."""
    timber_platform_ids = {platform.id for platform in scene.platforms if _is_timber(platform, scene)}
    timber_stair_ids = {stair.id for stair in scene.stairs if _is_timber(stair, scene)}
    has_terrain = bool(scene.terrain and scene.terrain.profiles)
    if not timber_platform_ids and not timber_stair_ids and not has_terrain:
        return model

    changed = False
    parts = []
    for part in model.parts:
        category = part.category
        placement = part.placement_id
        if placement.startswith("scene-terrain:"):
            category = "terrain"
        elif any(placement.startswith(f"scene-platform:{item_id}:") for item_id in timber_platform_ids):
            category = "timber"
        elif any(placement.startswith(f"scene-stair:{item_id}:") for item_id in timber_stair_ids):
            category = "timber"

        if category != part.category:
            changed = True
            parts.append(part.model_copy(update={"category": category}))
        else:
            parts.append(part)
    return model.model_copy(update={"parts": parts}) if changed else model
