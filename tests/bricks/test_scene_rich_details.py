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


def test_grade_below_building_datum_shifts_building_instead_of_flattening_terrain() -> None:
    payload=_scene().model_dump(mode="json")
    payload["terrain"]["profiles"][0]["start_elevation"]=-1.5
    payload["terrain"]["profiles"][0]["end_elevation"]=0.0
    scene=ArchitecturalScene.model_validate(payload)
    model=augment_brick_model_with_scene_architecture(_base_model(),scene,front_width_studs=48)
    terrain=[part for part in model.parts if part.placement_id.startswith("scene-terrain:right:")]
    wall=next(part for part in model.parts if part.placement_id=="wall-seed")
    assert min(part.z_plates for part in terrain)==0
    assert max(part.z_plates for part in terrain)>0
    # The architectural building datum is above the lower terrain and therefore
    # must move upward in the non-negative LEGO coordinate system.
    assert wall.z_plates>0


def test_glass_blocks_and_glazed_door_become_transparent_scene_parts() -> None:
    model=augment_brick_model_with_scene_glazing(_base_model(),_scene(),front_width_studs=48)
    glass=[part for part in model.parts if part.placement_id.startswith("scene-glazing:right_glass_blocks:")]
    door=[part for part in model.parts if part.placement_id.startswith("scene-glazing:left_glazed_door:")]
    assert glass and all(part.category=="window_pane" for part in glass)
    assert door
    # "Glazed" proves transparent material, not a perimeter-frame geometry.
    assert {part.category for part in door}=={"window_pane"}


def test_glazing_respects_scene_origin_when_terrain_falls_below_building() -> None:
    payload=_scene().model_dump(mode="json")
    payload["terrain"]["profiles"][0]["start_elevation"]=-1.5
    payload["terrain"]["profiles"][0]["end_elevation"]=0.0
    scene=ArchitecturalScene.model_validate(payload)
    architecture=augment_brick_model_with_scene_architecture(_base_model(),scene,front_width_studs=48)
    model=augment_brick_model_with_scene_glazing(architecture,scene,front_width_studs=48)
    glass=[part for part in model.parts if part.placement_id.startswith("scene-glazing:right_glass_blocks:")]
    assert glass
    # Building and opening must both be shifted above the negative terrain datum.
    wall=next(part for part in model.parts if part.placement_id=="wall-seed")
    assert min(part.z_plates for part in glass) == wall.z_plates


def test_scene_glazing_uses_the_openings_own_secondary_volume() -> None:
    payload=_scene().model_dump(mode="json")
    payload["terrain"]=None
    payload["volumes"].append({
        "id":"volume_second",
        "position":{"x":12,"y":2,"z":1},
        "width":{"value":4,"source":{"kind":"inferred","confidence":.7}},
        "depth":{"value":5,"source":{"kind":"inferred","confidence":.7}},
        "height":{"value":3,"source":{"kind":"inferred","confidence":.7}},
        "floors":1,
        "source":{"kind":"inferred","confidence":.7},
    })
    payload["openings"]=[{
        "id":"secondary_glazed_door","type":"door","volume_id":"volume_second","facade":"front",
        "offset_horizontal":1,"offset_vertical":.5,"width":1,"height":1.5,
        "source":{"kind":"inferred","confidence":.7},
        "evidence":[{"photo_index":3,"observation":"glazed door on secondary volume"}],
    }]
    scene=ArchitecturalScene.model_validate(payload)
    model=augment_brick_model_with_scene_glazing(_base_model(),scene,front_width_studs=50)
    parts=[part for part in model.parts if part.placement_id.startswith("scene-glazing:secondary_glazed_door:")]
    assert parts
    # Main width is 10m at 5 studs/m; secondary x=12m, so its front glazing must
    # start beyond the main volume rather than being projected onto x~=5.
    assert min(part.x_studs for part in parts) >= 60
    # Secondary volume is raised 1m and the opening begins another .5m above it.
    assert min(part.z_plates for part in parts) > 0
