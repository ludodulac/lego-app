import copy
import pytest
from brickhouse.bricks.building_layout import BuildingBrickShell, BuildingWallLayout
from brickhouse.bricks.placement import generate_simple_wall_layout
from brickhouse.bricks.roof import create_m0_roof_catalog, generate_spatial_gable_roof, validate_roof_support
from brickhouse.bricks.scaling import WallGridSpec
from brickhouse.building.models import Facade, RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, Point3D, RoofPlaneGeometry

def _wall_record(facade,width,height=6):
    grid=WallGridSpec(wall_id=f"v:{facade.value}",width_studs=width,height_bricks=height,studs_per_meter=1.0,courses_per_meter=1.0,openings=[])
    return BuildingWallLayout(wall_id=grid.wall_id,facade=facade,grid=grid,layout=generate_simple_wall_layout(width,height))
def _shell(width=10,depth=8,height=6):
    return BuildingBrickShell(building_id="b",volume_id="v",reference_width_studs=width,studs_per_meter=1.0,walls=[_wall_record(Facade.FRONT,width,height),_wall_record(Facade.REAR,width,height),_wall_record(Facade.LEFT,depth,height),_wall_record(Facade.RIGHT,depth,height)])
def _geometry(d):
    if d is RidgeDirection.DEPTH:
        n=[Point3D(x=0,y=0,z=6),Point3D(x=5,y=0,z=9),Point3D(x=5,y=8,z=9),Point3D(x=0,y=8,z=6)];p=[Point3D(x=5,y=0,z=9),Point3D(x=10,y=0,z=6),Point3D(x=10,y=8,z=6),Point3D(x=5,y=8,z=9)]
    else:
        n=[Point3D(x=0,y=0,z=6),Point3D(x=10,y=0,z=6),Point3D(x=10,y=4,z=9),Point3D(x=0,y=4,z=9)];p=[Point3D(x=0,y=4,z=9),Point3D(x=10,y=4,z=9),Point3D(x=10,y=8,z=6),Point3D(x=0,y=8,z=6)]
    return BuildingGeometry(building_id="b",walls=[],roof_planes=[RoofPlaneGeometry(id="r:n",roof_id="r",volume_id="v",roof_type=RoofType.GABLE,side="negative",ridge_direction=d,corners=n),RoofPlaneGeometry(id="r:p",roof_id="r",volume_id="v",roof_type=RoofType.GABLE,side="positive",ridge_direction=d,corners=p)])
def test_roof_catalog_uses_existing_piece_family_ids():
    c=create_m0_roof_catalog();s=c.get("BRICK_SLOPED_45_2X4")
    assert s.category=="roof_tile" and s.width_studs==2 and s.connection_overlap_studs==1
    assert c.get("TILE_1X4").category=="ridge_tile"
@pytest.mark.parametrize("d",[RidgeDirection.DEPTH,RidgeDirection.WIDTH])
def test_gable_roof_supports_both_ridge_directions(d):
    shell=_shell();roof=generate_spatial_gable_roof(_geometry(d),shell);assert roof.ridge_direction is d;assert any(p.side=="ridge" for p in roof.placements);validate_roof_support(roof,shell)
def test_eave_courses_are_anchored_on_wall_top():
    roof=generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),_shell());n=min((p for p in roof.placements if p.side=="negative"),key=lambda p:p.x_studs);p=max((p for p in roof.placements if p.side=="positive"),key=lambda p:p.x_studs);assert (n.x_studs,n.z_plates)==(0,18);assert (p.x_studs,p.z_plates)==(8,18)
def test_no_duplicate_spatial_slope_placements_at_center():
    roof=generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),_shell());keys=[(p.part_id,p.x_studs,p.y_studs,p.z_plates,p.rotation_quarter_turns) for p in roof.placements if p.side!="ridge"];assert len(keys)==len(set(keys))
def test_validator_rejects_a_floating_course():
    shell=_shell();broken=copy.deepcopy(generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),shell))
    for p in broken.placements:
        if p.side=="negative" and p.x_studs==2:p.x_studs+=2
    with pytest.raises(ValueError,match="floating roof course"):validate_roof_support(broken,shell)
def test_validator_rejects_vertical_jump_beyond_connection_limit():
    shell=_shell();broken=copy.deepcopy(generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),shell))
    for p in broken.placements:
        if p.side=="negative" and p.x_studs==1:p.z_plates+=20
    with pytest.raises(ValueError,match="vertical jump"):validate_roof_support(broken,shell)
def test_generation_is_deterministic():
    assert generate_spatial_gable_roof(_geometry(RidgeDirection.WIDTH),_shell()).model_dump(mode="json")==generate_spatial_gable_roof(_geometry(RidgeDirection.WIDTH),_shell()).model_dump(mode="json")
def test_non_gable_or_missing_planes_are_rejected():
    with pytest.raises(ValueError,match="exactly two"):generate_spatial_gable_roof(BuildingGeometry(building_id="b",walls=[],roof_planes=[]),_shell())
