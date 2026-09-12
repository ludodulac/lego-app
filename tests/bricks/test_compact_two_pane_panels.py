import json
from brickhouse.scene import ArchitecturalScene, project_scene_to_building
from brickhouse.pipeline import run_m0_pipeline_model

IDS=("obs-front-opening-top-left","obs-front-opening-top-right","obs-front-opening-middle-left","obs-front-opening-middle-right")

def test_real_two_pane_windows_use_compact_panel_family():
    source=ArchitecturalScene.model_validate(json.load(open("tests/fixtures/real_house_scene_pane_count_stage2.json",encoding="utf-8")))
    volume=next(v for v in source.volumes if v.id=="volume_main")
    openings=[next(o for o in source.openings if o.id==oid) for oid in IDS]
    micro=source.model_copy(update={"volumes":[volume],"openings":openings,"roofs":[],"terrain":None,"chimneys":[],"platforms":[],"stairs":[],"equipment":[],"visibility":[],"relations":[],"platform_structure_observations":[],"wall_profile_observations":[],"stair_system_links":[]})
    projected=project_scene_to_building(micro)
    assert projected.building is not None and not projected.blocked
    bundle=run_m0_pipeline_model(projected.building,front_width_studs=48)
    for oid in IDS:
        parts=[p for p in bundle.brick_model.parts if p.opening_id==oid]
        assert len(parts) in {14,15}
        assert {p.part_id for p in parts} <= {"PANEL_1X4X3_60581","PANEL_1X4X2_8012","BRICK_1X1"}
        assert sum(p.part_id.startswith("PANEL_") for p in parts)==6


def test_exact_compact_reservations_do_not_move_real_rasters():
    from brickhouse.geometry import generate_building_geometry
    from brickhouse.bricks import generate_building_brick_shell, build_opening_representation_plan, apply_opening_representation_plan
    source=ArchitecturalScene.model_validate(json.load(open("tests/fixtures/real_house_scene_pane_count_stage2.json",encoding="utf-8")))
    volume=next(v for v in source.volumes if v.id=="volume_main")
    openings=[next(o for o in source.openings if o.id==oid) for oid in IDS]
    micro=source.model_copy(update={"volumes":[volume],"openings":openings,"roofs":[],"terrain":None,"chimneys":[],"platforms":[],"stairs":[],"equipment":[],"visibility":[],"relations":[],"platform_structure_observations":[],"wall_profile_observations":[],"stair_system_links":[]})
    projected=project_scene_to_building(micro); assert projected.building is not None
    shell=generate_building_brick_shell(generate_building_geometry(projected.building),48)
    before={r.id:(r.x_studs,r.z_bricks,r.width_studs,r.height_bricks) for w in shell.walls for r in w.grid.openings if r.id in IDS}
    plan=build_opening_representation_plan(projected.building,shell)
    result=apply_opening_representation_plan(projected.building,shell,plan)
    after={r.id:(r.x_studs,r.z_bricks,r.width_studs,r.height_bricks) for w in result.shell.walls for r in w.grid.openings if r.id in IDS}
    assert not result.rejections
    assert before == after
    assert all(not a.geometry_changed for a in result.anchors if a.opening_id in IDS)
