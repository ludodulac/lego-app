from brickhouse.bricks.brick_model import BrickModel,BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene

def _base_model():
    return BrickModel(building_id="house",volume_id="volume_main",width_studs=48,depth_studs=48,height_plates=60,parts=[BrickModelPart(placement_id="wall-1",part_id="BRICK_1X1",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade=Facade.FRONT)])
def _scene():
    return ArchitecturalScene.model_validate({"schema_version":"0.2","id":"house","name":"Composite exterior architecture","units":"m","volumes":[{"id":"volume_main","position":{"x":0,"y":0,"z":0},"width":{"value":10,"source":{"kind":"user_provided","confidence":1}},"depth":{"value":10,"source":{"kind":"inferred","confidence":.5}},"height":{"value":7,"source":{"kind":"inferred","confidence":.5}},"floors":3,"source":{"kind":"inferred","confidence":.6}}],"platforms":[{"id":"stair_landing_concrete_01","position":{"x":-1.2,"y":8.3,"z":1.2},"width":1.2,"depth":1.3,"thickness":.25,"material":"concrete","edges":{"x_min":{"treatment":"solid_parapet"},"x_max":{"treatment":"access_opening"},"y_min":{"treatment":"solid_parapet"},"y_max":{"treatment":"solid_parapet"}},"source":{"kind":"inferred","confidence":.6},"evidence":[{"photo_index":1,"observation":"palier maçonné en béton avec muret"}]},{"id":"terrace_timber_01","position":{"x":-2.5,"y":3.0,"z":2.4},"width":2.5,"depth":5.3,"thickness":.2,"material":"timber","deck_board_direction":"y","supports":[{"id":"terrace_post_01","position":{"x":-2.4,"y":3.2,"z":0},"width":.15,"depth":.15,"height":2.4,"source":{"kind":"observed","confidence":.9}}],"edges":{"x_min":{"treatment":"open_railing"},"x_max":{"treatment":"wall_attached"},"y_min":{"treatment":"open_railing"},"y_max":{"treatment":"open_railing","access_spans":[{"from":.6,"to":1.7}]}},"source":{"kind":"inferred","confidence":.6},"evidence":[{"photo_index":2,"observation":"grande terrasse en bois sur poteaux"}]}],"stairs":[{"id":"stair_run_concrete_01","start":{"x":-1.0,"y":7.0,"z":0},"end":{"x":-1.0,"y":8.3,"z":1.2},"width":1.1,"material":"concrete","left_edge":"solid_parapet","right_edge":"solid_parapet","source":{"kind":"inferred","confidence":.6},"evidence":[{"photo_index":1,"observation":"première volée maçonnée avec rampes béton"}]},{"id":"stair_run_concrete_02","start":{"x":-1.0,"y":8.3,"z":1.2},"end":{"x":-1.0,"y":7.2,"z":2.4},"width":1.1,"material":"concrete","left_edge":"solid_parapet","right_edge":"none","source":{"kind":"inferred","confidence":.6},"evidence":[{"photo_index":2,"observation":"seconde volée maçonnée retournant vers la terrasse"}]}],"appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},"notes":"Escalier béton en deux volées avec palier; terrasse bois distincte."})
def test_composite_stair_runs_and_timber_deck_survive_to_brick_model():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene(),front_width_studs=48);ids=[p.placement_id for p in model.parts]
    assert any(v.startswith("scene-stair:stair_run_concrete_01:body:") for v in ids)
    assert any(v.startswith("scene-stair:stair_run_concrete_01:left-parapet:") for v in ids)
    assert any(v.startswith("scene-platform:stair_landing_concrete_01:x_min:parapet:") for v in ids)
    assert any(v.startswith("scene-platform:terrace_timber_01:board:") for v in ids)
    assert any("scene-platform:terrace_timber_01:support" in v for v in ids)
def test_timber_platform_uses_long_directional_boards_not_solid_masonry_fill():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene(),front_width_studs=48);boards=[p for p in model.parts if p.placement_id.startswith("scene-platform:terrace_timber_01:board:")]
    assert boards
    assert len({p.z_plates for p in boards})==1
    assert any(p.part_id!="BRICK_1X1" for p in boards)
    assert all(p.rotation_quarter_turns==0 for p in boards if p.part_id!="BRICK_1X1")
def test_wall_attached_edge_has_no_railing_and_access_span_breaks_outer_railing():
    model=augment_brick_model_with_scene_architecture(_base_model(),_scene(),front_width_studs=48);ids=[p.placement_id for p in model.parts]
    assert not any(":x_max:rail" in v for v in ids if "terrace_timber_01" in v)
    outer=[p for p in model.parts if "terrace_timber_01:y_max:rail-top" in p.placement_id]
    assert outer
    xs=sorted(p.x_studs for p in outer)
    assert any(b-a>1 for a,b in zip(xs,xs[1:]))
