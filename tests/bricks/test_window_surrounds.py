from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry
from brickhouse.bricks.windows import generate_window_assemblies
from brickhouse.building.models import BuildingModel
from brickhouse.geometry import generate_building_geometry


def _building(*, decorative=True, sill=True, surround_material=None, surround_color=None):
    opening = {
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
    }
    visual = {}
    if surround_material is not None:
        visual["surround_material"] = surround_material
    if surround_color is not None:
        visual["surround_color"] = surround_color
    if visual:
        opening["opening_visual"] = visual
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
        "openings":[opening],
        "roofs":[],
        "appearance":{
            "walls":{"color":"off_white"},
            "frames":{"color":"stone"},
        },
        "metadata":{"created_from":"photo_analysis"},
    })


def _shell(building):
    return generate_building_brick_shell(generate_building_geometry(building), front_width_studs=32)


def _front_occupied_cells(details):
    catalog = create_m0_brick_catalog()
    occupied = set()
    for placement in details:
        if placement.facade.value != "front":
            continue
        brick = catalog.get(placement.part_id)
        width, depth = brick.footprint(placement.rotation_quarter_turns)
        assert depth == 1
        for dx in range(width):
            occupied.add((placement.x_studs + dx, placement.z_plates // 3))
    return occupied


def test_decorative_surround_never_places_masonry_inside_window_void():
    building=_building()
    shell=_shell(building)
    details=generate_window_surrounds(building,shell)
    front=next(w for w in shell.walls if w.facade.value=="front")
    raster=front.grid.openings[0]
    occupied=_front_occupied_cells(details)
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


def test_horizontal_semantic_trim_compacts_complete_architectural_ring():
    building = _building()
    shell = _shell(building)
    details = generate_window_surrounds(building, shell)
    front = next(w for w in shell.walls if w.facade.value == "front")
    raster = front.grid.openings[0]

    left = raster.x_studs - 1
    right = raster.x_studs + raster.width_studs
    bottom = raster.z_bricks - 1
    top = raster.z_bricks + raster.height_bricks
    expected = {
        (left, course)
        for course in range(bottom, top + 1)
    } | {
        (right, course)
        for course in range(bottom, top + 1)
    } | {
        (x, bottom)
        for x in range(raster.x_studs, raster.x_studs + raster.width_studs)
    } | {
        (x, top)
        for x in range(raster.x_studs, raster.x_studs + raster.width_studs)
    }

    assert _front_occupied_cells(details) == expected

    horizontal = [
        placement
        for placement in details
        if placement.trim_role in {"sill", "head", "surround_base"}
    ]
    assert horizontal
    assert any(placement.part_id != "BRICK_1X1" for placement in horizontal)
    assert len(horizontal) < raster.width_studs * 2
    assert {placement.opening_id for placement in horizontal} == {"w1"}


def test_vertical_jambs_stay_upright_1x1_until_sideways_technique_is_approved():
    building = _building()
    shell = _shell(building)
    details = generate_window_surrounds(building, shell)

    jambs = [
        placement
        for placement in details
        if placement.trim_role in {"left_jamb", "right_jamb"}
    ]
    assert jambs
    assert {placement.part_id for placement in jambs} == {"BRICK_1X1"}
    assert {placement.rotation_quarter_turns for placement in jambs} == {0}


def test_compacted_trim_uses_only_placement_approved_canonical_parts():
    building = _building()
    shell = _shell(building)
    details = generate_window_surrounds(building, shell)
    approved = create_current_engine_capability_registry().approved_ids()

    assert {placement.part_id for placement in details} <= approved


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


def test_stone_like_surround_is_conservatively_masonry_but_sill_stays_generic():
    building = _building(surround_material="stone_like")
    details = generate_window_surrounds(building, _shell(building))

    surround = [p for p in details if p.trim_role in {"left_jamb", "right_jamb", "head", "surround_base"}]
    sill = [p for p in details if p.trim_role == "sill"]
    assert surround
    assert {p.category for p in surround} == {"masonry"}
    assert sill
    assert {p.category for p in sill} == {"facade_detail"}


def test_explicit_stone_surround_uses_stone_category():
    building = _building(sill=False, surround_material="natural stone")
    details = generate_window_surrounds(building, _shell(building))

    assert details
    assert {p.category for p in details} == {"stone"}
    assert {p.trim_role for p in details} >= {"left_jamb", "right_jamb", "head", "surround_base"}


def test_unknown_surround_material_remains_generic_instead_of_guessing():
    building = _building(sill=False, surround_material="decorative_unknown_finish")
    details = generate_window_surrounds(building, _shell(building))

    assert details
    assert {p.category for p in details} == {"facade_detail"}


def test_observed_surround_color_is_carried_only_by_surround_roles():
    building = _building(
        sill=True,
        surround_material="stone_like",
        surround_color="slightly darker beige",
    )
    details = generate_window_surrounds(building, _shell(building))

    surround = [p for p in details if p.trim_role in {"left_jamb", "right_jamb", "head", "surround_base"}]
    sill = [p for p in details if p.trim_role == "sill"]
    assert surround
    assert {p.semantic_color for p in surround} == {"slightly darker beige"}
    assert sill
    assert {p.semantic_color for p in sill} == {None}


def test_surround_color_does_not_imply_material_category():
    building = _building(sill=False, surround_color="gray")
    details = generate_window_surrounds(building, _shell(building))

    assert details
    assert {p.category for p in details} == {"facade_detail"}
    assert {p.semantic_color for p in details} == {"gray"}
