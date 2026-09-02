"""Apply Scene material semantics to rich BrickModel exterior parts."""
from __future__ import annotations

from brickhouse.scene.models import ArchitecturalScene, ExteriorMaterial

from .brick_model import BrickModel
from .scene_access import validate_scene_stair_platform_access
from .scene_architecture import _is_timber
from .scene_railing_solutions import compact_scene_platform_railings


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
    """Validate exterior access, reclassify parts, then apply rail solutions.

    Access validation deliberately happens before railing compaction: a stair may
    not silently punch through an explicitly guarded platform edge. The source
    Scene must declare an access span wide enough for the stair before a LEGO
    representation is accepted.

    Railing compaction runs after classification so replacing a run of generated
    1x1 rail cells with approved 1xN bricks preserves the Scene's timber/metal/etc.
    semantics. The geometry change itself lives in the separate
    ``scene_railing_solutions`` module rather than in material inference.
    """
    validate_scene_stair_platform_access(scene)

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

    categorized = model.model_copy(update={"parts": parts}) if changed else model
    # This remains a no-op when the Scene generated no compactable platform rail.
    return compact_scene_platform_railings(categorized, scene)
