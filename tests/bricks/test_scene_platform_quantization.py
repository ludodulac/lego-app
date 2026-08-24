from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


def _base_model():
    return BrickModel(
        building_id="quantization",
        volume_id="volume_main",
        width_studs=48,
        depth_studs=54,
        height_plates=60,
        parts=[BrickModelPart(
            placement_id="seed", part_id="BRICK_1X1", category="brick", component="wall",
            x_studs=0, y_studs=0, z_plates=0, rotation_quarter_turns=0, facade=Facade.FRONT,
        )],
    )


def _scene():
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"quantization","name":"Quantization","units":"m",
        "volumes":[{
            "id":"volume_main","position":{"x":0,"y":0,"z":0},
            "width":{"value":10,"source":{"kind":"user_provided","confidence":1}},
            "depth":{"value":11.25,"source":{"kind":"inferred","confidence":.6}},
            "height":{"value":7,"source":{"kind":"inferred","confidence":.6}},
            "floors":2,"source":{"kind":"inferred","confidence":.6},
        }],
        "platforms":[{
            "id":"upper_transition","position":{"x":-1.2,"y":8.9,"z":2.45},
            "width":1.2,"depth":.85,"thickness":.28,"material":"concrete",
            "edges":{
                "x_min":{"treatment":"solid_parapet","access_spans":[{"from":0,"to":.85}]},
                "x_max":{"treatment":"wall_attached"},
                "y_min":{"treatment":"solid_parapet","access_spans":[{"from":0,"to":1.2}]},
                "y_max":{"treatment":"solid_parapet"},
            },
            "source":{"kind":"inferred","confidence":.5},
        }],
        "stairs":[{
            "id":"upper_stair","start":{"x":-2.35,"y":9.35,"z":0},
            "end":{"x":-1.2,"y":9.35,"z":2.45},"width":1.0,"material":"concrete",
            "left_edge":"solid_parapet","right_edge":"none",
            "source":{"kind":"inferred","confidence":.5},
        }],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def test_walkable_platform_extent_is_never_rounded_smaller_than_metric_extent():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene(),front_width_studs=48)
    deck=[part for part in model.parts if part.placement_id.startswith("scene-platform:upper_transition:deck:")]
    assert deck
    # 0.85m at 4.8 studs/m is 4.08 studs. A walkable landing must therefore
    # occupy at least five stud rows, never be rounded down to four.
    assert len({part.y_studs for part in deck}) >= 5


def test_quantized_platform_covers_the_connected_stair_tread_cross_span():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene(),front_width_studs=48)
    deck=[part for part in model.parts if part.placement_id.startswith("scene-platform:upper_transition:deck:")]
    end_treads=[
        part for part in model.parts
        if part.placement_id.startswith("scene-stair:upper_stair:tread:")
        and part.z_plates == max(
            p.z_plates for p in model.parts if p.placement_id.startswith("scene-stair:upper_stair:tread:")
        )
    ]
    assert end_treads
    platform_y={part.y_studs for part in deck}
    stair_y={part.y_studs for part in end_treads}
    assert stair_y <= platform_y
