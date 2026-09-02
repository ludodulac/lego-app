"""Apply Scene material semantics to rich BrickModel exterior parts."""
from __future__ import annotations

from brickhouse.scene.models import ArchitecturalScene, ExteriorMaterial

from .brick_model import BrickModel
from .scene_access import validate_scene_stair_platform_access
from .scene_architecture import _is_timber
from .scene_railing_solutions import compact_scene_platform_railings
from .scene_stair_body_solutions import compact_scene_stair_bodies
from .scene_stair_solutions import compact_scene_stair_treads
from .scene_support_solutions import compact_scene_platform_supports


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
    """Validate access, classify exterior parts, then apply structural solutions.

    Access validation deliberately happens before railing compaction: a stair may
    not silently punch through an explicitly guarded platform edge. The source
    Scene must declare an access span wide enough for the stair before a LEGO
    representation is accepted.

    Railing, support, tread and masonry-body compaction run after classification
    so replacement bricks preserve the Scene's timber/metal/etc. semantics. Every
    solution layer only exact-covers already-generated cells; none may invent
    missing architectural geometry.
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
    # These remain no-ops when the Scene generated no eligible cells.
    railing_compacted = compact_scene_platform_railings(categorized, scene)
    support_compacted = compact_scene_platform_supports(railing_compacted, scene)
    body_compacted = compact_scene_stair_bodies(support_compacted, scene)
    return compact_scene_stair_treads(body_compacted, scene)
