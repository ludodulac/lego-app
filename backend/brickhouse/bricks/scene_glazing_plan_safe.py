"""Production-safe Scene glazing after explicit opening representation planning.

The historical Scene glazing helper can synthesize visible glazing from BRICK_1X1
cells. That remains useful for the dedicated glass-block representation, but a
proven glazed door or semantically unresolved glazed opening must now be handled
by LEGORepresentationPlan before wall infill. This wrapper therefore limits the
legacy augmenter to glass-block targets only.
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

    Door/UNKNOWN clear glazing is deliberately absent here: if the representation
    plan found a validated motif, it is already present in ``model``; if it did
    not, the pipeline preserves the void and reports a fidelity issue rather than
    fabricating transparent-looking BRICK_1X1 cells.

    Glass blocks are different: their visible grid is material rather than framed
    joinery. They are therefore allowed to replace a generic window representation
    that may have been emitted earlier from a BuildingModel projection that lost
    the Scene evidence text identifying glass blocks.
    """
    glass_block_openings = [
        opening for opening in scene.openings if _is_glass_block(opening)
    ]
    if not glass_block_openings:
        return model

    glass_block_scene = scene.model_copy(update={"openings": glass_block_openings})
    return augment_brick_model_with_scene_glazing(
        model,
        glass_block_scene,
        front_width_studs=front_width_studs,
    )
