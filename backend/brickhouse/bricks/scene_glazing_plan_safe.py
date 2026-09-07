"""Production-safe Scene glazing after explicit opening representation planning.

The historical Scene glazing helper can synthesize visible glazing from BRICK_1X1
cells. That remains useful for the dedicated glass-block representation, but a
proven glazed door or semantically unresolved glazed opening must now be handled
by LEGORepresentationPlan before wall infill. This wrapper therefore limits the
legacy augmenter to glass-block targets and prevents it from overwriting planned
frame/pane assemblies.
"""
from __future__ import annotations

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.scene_glazing import _is_glass_block, augment_brick_model_with_scene_glazing
from brickhouse.scene import ArchitecturalScene


def augment_brick_model_with_planned_scene_glazing(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Apply only legacy glass-block glazing after planned openings are emitted.

    Door/UNKNOWN glazing is deliberately absent here: if the representation plan
    found a validated motif, it is already present in ``model``; if it did not,
    the pipeline must preserve the architectural void and report a fidelity issue
    rather than fabricating transparent-looking BRICK_1X1 cells.
    """
    represented_opening_ids = {
        part.opening_id
        for part in model.parts
        if part.opening_id is not None
        and part.category in {"window_frame", "window_pane"}
    }
    glass_block_openings = [
        opening
        for opening in scene.openings
        if opening.id not in represented_opening_ids and _is_glass_block(opening)
    ]
    if not glass_block_openings:
        return model

    glass_block_scene = scene.model_copy(update={"openings": glass_block_openings})
    return augment_brick_model_with_scene_glazing(
        model,
        glass_block_scene,
        front_width_studs=front_width_studs,
    )
