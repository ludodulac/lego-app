from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def test_glass_block_scene_replaces_generic_simple_window_fill_without_duplicate_cells():
    scene=ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"glass-block-replacement","name":"Glass block replacement","units":"m",
        "volumes":[{
            "id":"main","position":{"x":0,"y":0,"z":0},
            "width":{"value":10,"source":{"kind":"user_provided","confidence":1}},
            "depth":{"value":8,"source":{"kind":"inferred","confidence":.7}},
            "height":{"value":5,"source":{"kind":"inferred","confidence":.7}},
            "floors":2,"source":{"kind":"inferred","confidence":.7},
        }],
        "openings":[{
            "id":"glass_blocks","type":"window","volume_id":"main","facade":"right",
            "offset_horizontal":3,"offset_vertical":1,"width":1,"height":1,
            "window_style":"simple","source":{"kind":"inferred","confidence":.7},
            "evidence":[{"photo_index":1,"observation":"ouverture en pavés de verre"}],
        }],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })
    bundle=run_m0_pipeline_scene(scene,front_width_studs=50)
    scene_parts=[part for part in bundle.brick_model.parts if part.placement_id.startswith("scene-glazing:glass_blocks:")]
    assert scene_parts
    target_cells={(part.x_studs,part.y_studs,part.z_plates,part.facade) for part in scene_parts}
    occupants=[
        part for part in bundle.brick_model.parts
        if (part.x_studs,part.y_studs,part.z_plates,part.facade) in target_cells
        and part.component=="facade_detail"
    ]
    assert len(occupants)==len(target_cells)
    assert all(part.placement_id.startswith("scene-glazing:glass_blocks:") for part in occupants)
