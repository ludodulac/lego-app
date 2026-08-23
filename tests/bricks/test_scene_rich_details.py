from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.scene.models import ArchitecturalScene


def _base_model() -> BrickModel:
    return BrickModel(
        building_id="house",
        volume_id="volume_main",
        width_studs=48,
        depth_studs=48,
        height_plates=60,
        parts=[BrickModelPart(placement_id="wall-seed",part_id="BRICK_1X1",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade="front")],
    )


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"scene-rich","name":"Scene rich","units":"m",
        "volumes":[{"id":"volume_main","position":{"x":0,"y":0,"z":0},"width":{"value":10,"source":{"kind":"user_provided","confidence":1}},"depth":{"value":10,"source":{"kind":"inferred","confidence":.5}},"height":{"value":7,"source":{"kind":"inferred","confidence":.5}},"floors":3,"source":{"kind":"inferred","confidence":.6}}],
        "openings":[
            {"id":"right_glass_blocks","type":"window","volume_id":"volume_main","facade":"right","offset_horizontal":7,"offset_vertical":0,"width":1,"height":.75,"local_grade_clearance":0,"source":{"kind":"inferred","confidence":.6},"evidence":[{"photo_index":1,"observation":"ouverture basse en pavés de verre"}]},
            {"id":"left_glazed_door","type":"door","volume_id":"volume_main","facade":"left","offset_horizontal":3,"offset_vertical":2,"width":1.25,"height":2.25,"source":{"kind":"inferred","confidence":.6},"evidence":[{"photo_index":2,"observation":"porte-fenêtre vitrée au niveau terrasse"}]},
        ],
        "terrain":{"kind":"facade_grade_profiles","profiles":[{"facade":"right","start_elevation":0,"end_elevation":1.5,"outward_extent":1.5,"source":{"kind":"inferred","confidence":.5}}]},
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def test_grade_profile_survives_as_wide_stepped_terrain_surface() -> None:
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene(),front_width_studs=48)
    terrain=[part for part in model.parts if part.placement_id.startswith("scene-terrain:right:")]
    assert terrain
    assert all(part.category=="terrain" for part in terrain)
    assert max(part.z_plates for part in terrain)>min(part.z_plates for part in terrain)
    # 1.5m outward extent at 4.8 studs/m must occupy substantially more than a one-stud ribbon.
    assert len({part.x_studs for part in terrain})>=7


def test_glass_blocks_and_glazed_door_become_transparent_scene_parts() -> None:
    model=augment_brick_model_with_scene_glazing(_base_model(),_scene(),front_width_studs=48)
    glass=[part for part in model.parts if part.placement_id.startswith("scene-glazing:right_glass_blocks:")]
    door=[part for part in model.parts if part.placement_id.startswith("scene-glazing:left_glazed_door:")]
    assert glass and all(part.category=="window_pane" for part in glass)
    assert door
    assert {part.category for part in door}=={"window_frame","window_pane"}
