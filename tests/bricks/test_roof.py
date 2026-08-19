import copy

import pytest

from brickhouse.bricks.building_layout import BuildingBrickShell, BuildingWallLayout
from brickhouse.bricks.placement import generate_simple_wall_layout
from brickhouse.bricks.roof import create_m0_roof_catalog, generate_spatial_gable_roof, validate_roof_support
from brickhouse.bricks.scaling import WallGridSpec
from brickhouse.building.models import Facade, RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, Point3D, RoofPlaneGeometry


def _wall_record(facade, width, height=6):
    grid = WallGridSpec(wall_id=f"v:{facade.value}", width_studs=width, height_bricks=height, studs_per_meter=1.0, courses_per_meter=1.0, openings=[])
    return BuildingWallLayout(wall_id=grid.wall_id, facade=facade, grid=grid, layout=generate_simple_wall_layout(width, height))


def _shell(width=10, depth=8, height=6):
    return BuildingBrickShell(building_id="b", volume_id="v", reference_width_studs=width, studs_per_meter=1.0, walls=[_wall_record(Facade.FRONT,width,height), _wall_record(Facade.REAR,width,height), _wall_record(Facade.LEFT,depth,height), _wall_record(Facade.RIGHT,depth,height)])


def _geometry(ridge_direction):
    if ridge_direction is RidgeDirection.DEPTH:
        negative=[Point3D(x=0,y=0,z=6),Point3D(x=5,y=0,z=9),Point3D(x=5,y=8,z=9),Point3D(x=0,y=8,z=6)]
        positive=[Point3D(x=5,y=0,z=9),Point3D(x=10,y=0,z=6),Point3D(x=10,y=8,z=6),Point3D(x=5,y=8,z=9)]
    else:
        negative=[Point3D(x=0,y=0,z=6),Point3D(x=10,y=0,z=6),Point3D(x=10,y=4,z=9),Point3D(x=0,y=4,z=9)]
        positive=[Point3D(x=0,y=4,z=9),Point3D(x=10,y=4,z=9),Point3D(x=10,y=8,z=6),Point3D(x=0,y=8,z=6)]
    return BuildingGeometry(building_id="b", walls=[], roof_planes=[RoofPlaneGeometry(id="r:negative",roof_id="r",volume_id="v",roof_type=RoofType.GABLE,side="negative",ridge_direction=ridge_direction,corners=negative), RoofPlaneGeometry(id="r:positive",roof_id="r",volume_id="v",roof_type=RoofType.GABLE,side="positive",ridge_direction=ridge_direction,corners=positive)])


def test_roof_catalog_has_overlap_connectable_slopes_and_ridge_parts():
    catalog=create_m0_roof_catalog()
    slope=catalog.get("ROOF_SLOPE_2X8")
    assert slope.category=="roof_tile"
    assert slope.width_studs==2
    assert slope.connection_overlap_studs==1
    assert catalog.get("RIDGE_TILE_1X8").category=="ridge_tile"


@pytest.mark.parametrize("direction", [RidgeDirection.DEPTH,RidgeDirection.WIDTH])
def test_gable_roof_supports_both_ridge_directions(direction):
    shell=_shell(); roof=generate_spatial_gable_roof(_geometry(direction),shell)
    assert roof.ridge_direction is direction
    assert any(p.side=="ridge" for p in roof.placements)
    assert all(p.z_plates>=18 for p in roof.placements)
    validate_roof_support(roof,shell)


def test_eave_courses_are_anchored_on_wall_top():
    shell=_shell(); roof=generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),shell)
    negative=min((p for p in roof.placements if p.side=="negative"),key=lambda p:p.x_studs)
    positive=max((p for p in roof.placements if p.side=="positive"),key=lambda p:p.x_studs)
    assert negative.x_studs==0 and negative.z_plates==18
    assert positive.x_studs==8 and positive.z_plates==18


def test_consecutive_courses_overlap_one_stud_in_plan():
    roof=generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),_shell())
    catalog=create_m0_roof_catalog()
    courses={}
    for p in roof.placements:
        if p.side=="negative": courses.setdefault(p.x_studs,[]).append(p)
    axes=sorted(courses)
    def cells(ps):
        result=set()
        for p in ps:
            part=catalog.get(p.part_id)
            for dx in range(part.width_studs):
                for dy in range(part.length_studs): result.add((p.x_studs+dx,p.y_studs+dy))
        return result
    for left,right in zip(axes,axes[1:]):
        assert cells(courses[left]).intersection(cells(courses[right]))


def test_validator_rejects_a_floating_course():
    shell=_shell(); roof=generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),shell)
    broken=copy.deepcopy(roof)
    for p in broken.placements:
        if p.side=="negative" and p.x_studs==2: p.x_studs+=2
    with pytest.raises(ValueError,match="floating roof course"):
        validate_roof_support(broken,shell)


def test_validator_rejects_vertical_jump_beyond_connection_limit():
    shell=_shell(); roof=generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH),shell)
    broken=copy.deepcopy(roof)
    for p in broken.placements:
        if p.side=="negative" and p.x_studs==1: p.z_plates+=20
    with pytest.raises(ValueError,match="vertical jump"):
        validate_roof_support(broken,shell)


def test_generation_is_deterministic():
    first=generate_spatial_gable_roof(_geometry(RidgeDirection.WIDTH),_shell())
    second=generate_spatial_gable_roof(_geometry(RidgeDirection.WIDTH),_shell())
    assert first.model_dump(mode="json")==second.model_dump(mode="json")


def test_non_gable_or_missing_planes_are_rejected():
    with pytest.raises(ValueError,match="exactly two"):
        generate_spatial_gable_roof(BuildingGeometry(building_id="b",walls=[],roof_planes=[]),_shell())
