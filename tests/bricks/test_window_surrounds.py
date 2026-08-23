from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.bricks.windows import generate_window_assemblies
from brickhouse.building.models import BuildingModel
from brickhouse.geometry import generate_building_geometry


def _building(*, decorative=True, sill=True):
    return BuildingModel.model_validate({
        "schema_version":"0.1",
        "id":"house",
        "name":"Generic surround test",
        "building_type":"test",
        "units":"m",
        "volumes":[{
            "id":"main",
            "shape":"rectangular_prism",
            "position":{"x":0,"y":0,"z":0},
            "width":8,"depth":6,"height":6,"floors":2,
            "source":{"kind":"inferred","confidence":.8},
        }],
        "openings":[{
            "id":"w1",
            "type":"window",
            "volume_id":"main",
            "facade":"front",
            "offset_horizontal":2,
            "offset_vertical":2,
            "width":2,
            "height":2.4,
            "window_style":"simple",
            "has_sill":sill,
            "has_decorative_surround":decorative,
            "source":{"kind":"observed","confidence":.95},
        }],
        "roofs":[],
        "appearance":{
            "walls":{"color":"off_white"},
            "frames":{"color":"stone"},
        },
        "metadata":{"created_from":"photo_analysis"},
    })


def _shell(building):
    return generate_building_brick_shell(generate_building_geometry(building), front_width_studs=32)


def test_decorative_surround_never_places_masonry_inside_window_void():
    building=_building()
    shell=_shell(building)
    details=generate_window_surrounds(building,shell)
    front=next(w for w in shell.walls if w.facade.value=="front")
    raster=front.grid.openings[0]
    occupied={(p.x_studs,p.z_plates//3) for p in details if p.facade.value=="front"}
    void={
        (x,z)
        for x in range(raster.x_studs,raster.x_studs+raster.width_studs)
        for z in range(raster.z_bricks,raster.z_bricks+raster.height_bricks)
    }
    assert details
    assert occupied.isdisjoint(void)
    assert any(x==raster.x_studs-1 for x,_ in occupied)
    assert any(x==raster.x_studs+raster.width_studs for x,_ in occupied)
    assert any(z==raster.z_bricks+raster.height_bricks for _,z in occupied)


def test_real_lego_window_does_not_erase_observed_architectural_surround():
    building=_building()
    shell=_shell(building)
    _,fitted=generate_window_assemblies(building,shell)
    assert "w1" in fitted
    details=generate_window_surrounds(building,shell,skip_opening_ids=fitted)
    assert details


def test_no_surround_metadata_produces_no_generic_window_border():
    building=_building(decorative=False,sill=False)
    shell=_shell(building)
    assert generate_window_surrounds(building,shell)==[]
