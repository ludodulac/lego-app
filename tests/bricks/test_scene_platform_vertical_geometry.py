from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _base_model():
    return BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=50,
        depth_studs=40,
        height_plates=60,
        parts=[BrickModelPart(placement_id="wall",part_id="BRICK_1X1",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade=Facade.FRONT)],
    )


def _scene_with_concrete_landing_and_stair(level=1.2):
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"landing-scene","name":"Concrete landing vertical alignment",
        "volumes":[{"id":"main","position":{"x":0,"y":0,"z":0},"width":{"value":10,"source":SOURCE},"depth":{"value":8,"source":SOURCE},"height":{"value":6,"source":SOURCE},"floors":2,"source":SOURCE}],
        "platforms":[{"id":"landing","position":{"x":-1.0,"y":3.0,"z":level},"width":1.0,"depth":1.5,"thickness":0.4,"material":"concrete","source":SOURCE}],
        "stairs":[{"id":"run","start":{"x":-1.0,"y":1.5,"z":0},"end":{"x":-1.0,"y":3.0,"z":level},"width":0.8,"material":"concrete","source":SOURCE}],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def _scene_with_elevated_explicit_support():
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"support-scene","name":"Explicit support geometry",
        "volumes":[{"id":"main","position":{"x":0,"y":0,"z":0},"width":{"value":10,"source":SOURCE},"depth":{"value":8,"source":SOURCE},"height":{"value":6,"source":SOURCE},"floors":2,"source":SOURCE}],
        "platforms":[{"id":"deck","position":{"x":-1.0,"y":2.0,"z":2.0},"width":1.0,"depth":2.0,"thickness":0.2,"material":"timber","supports":[{"id":"post","position":{"x":-0.9,"y":2.2,"z":0.6},"width":0.45,"depth":0.45,"height":0.8,"source":SOURCE}],"source":SOURCE}],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def _connection_levels(model):
    landing=[p for p in model.parts if p.placement_id.startswith("scene-platform:landing:deck:")]
    treads=[p for p in model.parts if p.placement_id.startswith("scene-stair:run:tread:")]
    assert landing and treads
    return landing,treads,max(p.z_plates for p in treads)


def test_thick_masonry_landing_grows_downward_from_connection_level():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene_with_concrete_landing_and_stair(),front_width_studs=50)
    landing,treads,stair_connection_z=_connection_levels(model)
    assert max(p.z_plates for p in landing)==stair_connection_z
    assert min(p.z_plates for p in landing)<stair_connection_z
    assert not any(p.z_plates>stair_connection_z for p in landing)


def test_non_course_metric_level_quantizes_identically_for_landing_and_stair_endpoint():
    # At this scale 1.1m is not an exact 3-plate course before quantization. The
    # landing and stair must nevertheless choose the same LEGO level.
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene_with_concrete_landing_and_stair(level=1.1),front_width_studs=50)
    landing,_,stair_connection_z=_connection_levels(model)
    assert max(p.z_plates for p in landing)==stair_connection_z
    assert stair_connection_z%3==0


def test_explicit_support_uses_declared_base_height_and_does_not_stretch_to_ground():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene_with_elevated_explicit_support(),front_width_studs=50)
    supports=[p for p in model.parts if p.placement_id.startswith("scene-platform:deck:support1:")]
    assert supports
    assert min(p.z_plates for p in supports)>0
    assert max(p.z_plates for p in supports)<25
    assert len({(p.x_studs,p.y_studs) for p in supports})>1
