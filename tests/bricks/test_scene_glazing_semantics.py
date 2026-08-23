from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.scene import ArchitecturalScene


def test_explicit_non_glazed_door_is_not_filled_with_scene_glazing():
    scene=ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"unglazed","name":"Unglazed door","units":"m",
        "volumes":[{
            "id":"main","position":{"x":0,"y":0,"z":0},
            "width":{"value":10,"source":{"kind":"user_provided","confidence":1}},
            "depth":{"value":8,"source":{"kind":"inferred","confidence":.7}},
            "height":{"value":5,"source":{"kind":"inferred","confidence":.7}},
            "floors":2,"source":{"kind":"inferred","confidence":.7},
        }],
        "openings":[{
            "id":"service_door","type":"door","volume_id":"main","facade":"left",
            "offset_horizontal":2,"offset_vertical":0,"width":1.2,"height":2,
            "source":{"kind":"inferred","confidence":.7},
            "evidence":[{"photo_index":1,"observation":"Grande ouverture non vitrée d’accès."}],
        }],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })
    model=BrickModel(
        building_id="unglazed",volume_id="main",width_studs=48,depth_studs=38,height_plates=60,
        parts=[BrickModelPart(placement_id="seed",part_id="BRICK_1X1",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade="front")],
    )
    enriched=augment_brick_model_with_scene_glazing(model,scene,front_width_studs=48)
    assert enriched is model
    assert not any(part.placement_id.startswith("scene-glazing:service_door:") for part in enriched.parts)
