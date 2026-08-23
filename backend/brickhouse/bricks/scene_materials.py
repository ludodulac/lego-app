"""Apply Scene material semantics to rich BrickModel exterior parts."""
from __future__ import annotations

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel
from .scene_architecture import _is_timber


def apply_scene_part_categories(model: BrickModel, scene: ArchitecturalScene) -> BrickModel:
    """Reclassify generated exterior parts for viewer/BOM material distinction."""
    timber_platform_ids = {platform.id for platform in scene.platforms if _is_timber(platform, scene)}
    if not timber_platform_ids and not (scene.terrain and scene.terrain.profiles):
        return model

    changed = False
    parts = []
    for part in model.parts:
        category = part.category
        if part.placement_id.startswith("scene-terrain:"):
            category = "terrain"
        else:
            for platform_id in timber_platform_ids:
                if part.placement_id.startswith(f"scene-platform:{platform_id}:"):
                    category = "timber"
                    break
        if category != part.category:
            changed = True
            parts.append(part.model_copy(update={"category": category}))
        else:
            parts.append(part)
    return model.model_copy(update={"parts": parts}) if changed else model
