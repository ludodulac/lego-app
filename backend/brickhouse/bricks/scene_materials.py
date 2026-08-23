"""Apply Scene material semantics to rich BrickModel exterior parts."""
from __future__ import annotations

from brickhouse.scene.models import ArchitecturalScene, ExteriorMaterial

from .brick_model import BrickModel
from .scene_architecture import _is_timber


_MATERIAL_CATEGORY = {
    ExteriorMaterial.TIMBER: "timber",
    ExteriorMaterial.CONCRETE: "concrete",
    ExteriorMaterial.MASONRY: "masonry",
    ExteriorMaterial.STONE: "stone",
    ExteriorMaterial.METAL: "metal",
    ExteriorMaterial.COMPOSITE: "composite",
}


def _structured_category(obj, scene: ArchitecturalScene) -> str | None:
    material = getattr(obj, "material", None)
    if material in _MATERIAL_CATEGORY:
        return _MATERIAL_CATEGORY[material]
    # Preserve legacy timber inference only for older Scenes that lack material.
    if material is None and _is_timber(obj, scene):
        return "timber"
    return None


def apply_scene_part_categories(model: BrickModel, scene: ArchitecturalScene) -> BrickModel:
    """Reclassify generated exterior parts without guessing missing materials."""
    platform_categories = {
        platform.id: category
        for platform in scene.platforms
        if (category := _structured_category(platform, scene)) is not None
    }
    stair_categories = {
        stair.id: category
        for stair in scene.stairs
        if (category := _structured_category(stair, scene)) is not None
    }
    has_terrain = bool(scene.terrain and scene.terrain.profiles)
    if not platform_categories and not stair_categories and not has_terrain:
        return model

    changed = False
    parts = []
    for part in model.parts:
        category = part.category
        placement = part.placement_id
        if placement.startswith("scene-terrain:"):
            category = "terrain"
        else:
            for item_id, material_category in platform_categories.items():
                if placement.startswith(f"scene-platform:{item_id}:"):
                    category = material_category
                    break
            else:
                for item_id, material_category in stair_categories.items():
                    if placement.startswith(f"scene-stair:{item_id}:"):
                        category = material_category
                        break

        if category != part.category:
            changed = True
            parts.append(part.model_copy(update={"category": category}))
        else:
            parts.append(part)
    return model.model_copy(update={"parts": parts}) if changed else model
