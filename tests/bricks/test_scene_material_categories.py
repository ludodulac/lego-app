from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def _scene():
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"materials","name":"Exterior materials","units":"m",
        "volumes":[{
            "id":"main","position":{"x":0,"y":0,"z":0},
            "width":{"value":10,"source":{"kind":"user_provided","confidence":1}},
            "depth":{"value":8,"source":{"kind":"inferred","confidence":.7}},
            "height":{"value":6,"source":{"kind":"inferred","confidence":.7}},
            "floors":2,"source":{"kind":"inferred","confidence":.7},
        }],
        "platforms":[
            {
                "id":"wood_deck","position":{"x":-2,"y":1,"z":2},
                "width":2,"depth":2,"thickness":.2,"material":"timber",
                "deck_board_direction":"y","source":{"kind":"inferred","confidence":.7},
            },
            {
                "id":"concrete_landing","position":{"x":-1,"y":4,"z":1},
                "width":1,"depth":1,"thickness":.25,"material":"concrete",
                "source":{"kind":"inferred","confidence":.7},
            },
        ],
        "stairs":[{
            "id":"masonry_stair","start":{"x":-.5,"y":3,"z":0},
            "end":{"x":-.5,"y":4,"z":1},"width":.8,"material":"masonry",
            "source":{"kind":"inferred","confidence":.7},
        }],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def test_structured_exterior_materials_survive_to_final_brick_categories():
    bundle=run_m0_pipeline_scene(_scene(),front_width_studs=50)
    categories={
        part.placement_id: part.category
        for part in bundle.brick_model.parts
        if part.placement_id.startswith(("scene-platform:","scene-stair:"))
    }
    assert categories
    assert all(category=="timber" for pid,category in categories.items() if "wood_deck" in pid)
    assert all(category=="concrete" for pid,category in categories.items() if "concrete_landing" in pid)
    assert all(category=="masonry" for pid,category in categories.items() if "masonry_stair" in pid)
