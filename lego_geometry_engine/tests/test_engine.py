from pathlib import Path

import pytest

from lego_geometry_engine import (
    AABB,
    LDrawLibrary,
    PartDefinition,
    Relation,
    Transform,
    analyze_assembly,
    check_collision,
    instantiate,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ldraw"


@pytest.fixture(scope="module")
def lib():
    return LDrawLibrary(FIXTURE)


@pytest.fixture(scope="module")
def brick(lib):
    return lib.load_part("3005")


@pytest.fixture(scope="module")
def slope(lib):
    return lib.load_part("3037")


def _cube_definition(part_id: str, half_extent: float) -> PartDefinition:
    h = half_extent
    p000 = (-h, -h, -h)
    p001 = (-h, -h, h)
    p010 = (-h, h, -h)
    p011 = (-h, h, h)
    p100 = (h, -h, -h)
    p101 = (h, -h, h)
    p110 = (h, h, -h)
    p111 = (h, h, h)
    triangles = (
        (p000, p100, p110), (p000, p110, p010),
        (p001, p011, p111), (p001, p111, p101),
        (p000, p001, p101), (p000, p101, p100),
        (p010, p110, p111), (p010, p111, p011),
        (p000, p010, p011), (p000, p011, p001),
        (p100, p101, p111), (p100, p111, p110),
    )
    return PartDefinition(part_id, triangles, AABB((-h, -h, -h), (h, h, h)))


def test_a_separated_bricks(brick):
    a = instantiate(brick, "a")
    b = instantiate(brick, "b", Transform.translation(40, 0, 0))
    assert check_collision(a, b) is Relation.SEPARATED


def test_b_coincident_bricks_collide(brick):
    assert check_collision(instantiate(brick, "a"), instantiate(brick, "b")) is Relation.COLLISION


def test_c_stacked_bricks_contact_not_collision(brick):
    a = instantiate(brick, "lower")
    b = instantiate(brick, "upper", Transform.translation(0, -24, 0))
    assert check_collision(a, b) is Relation.CONTACT


def test_d_wall_under_real_slope_has_no_collision(brick, slope):
    roof = instantiate(slope, "roof-17")
    wall = instantiate(brick, "wall-42", Transform.translation(0, -24, -10))
    assert check_collision(roof, wall) is Relation.CONTACT


def test_e_wall_penetrates_real_slope_is_collision(brick, slope):
    roof = instantiate(slope, "roof-17")
    wall = instantiate(brick, "wall-42", Transform.translation(0, -20, -10))
    assert check_collision(roof, wall) is Relation.COLLISION
    report = analyze_assembly([roof, wall])
    assert {report.collisions[0]["part_a"], report.collisions[0]["part_b"]} == {"roof-17", "wall-42"}


def test_f_small_valid_construction(brick):
    parts = [
        instantiate(brick, "b0"),
        instantiate(brick, "b1", Transform.translation(0, -24, 0)),
        instantiate(brick, "b2", Transform.translation(0, -48, 0)),
    ]
    report = analyze_assembly(parts)
    assert report.valid is True
    assert not report.collisions
    assert not report.unsupported_parts
    assert report.connections


def test_g_floating_part_reported(brick):
    parts = [
        instantiate(brick, "b0"),
        instantiate(brick, "b1", Transform.translation(0, -24, 0)),
        instantiate(brick, "floating", Transform.translation(40, -48, 0)),
    ]
    report = analyze_assembly(parts)
    assert report.valid is False
    assert report.unsupported_parts == ["floating"]


def test_recursive_transform_and_definition_cache(lib):
    a = lib.load_part("3005")
    b = lib.load_part("3005.dat")
    assert a is b
    assert len(a.triangles) > 12


def test_full_stud_geometry_keeps_connectors_on_nominal_mating_planes(brick):
    # The official stud protrudes 4 LDU above the brick body. Connector
    # semantics belong to the body mating planes, not the mesh extrema.
    assert brick.bbox.minimum[1] == pytest.approx(-4.0)
    assert brick.bbox.maximum[1] == pytest.approx(24.0)
    stud = next(connector for connector in brick.connectors if connector.type == "stud")
    anti_stud = next(connector for connector in brick.connectors if connector.type == "anti_stud")
    assert stud.position[1] == pytest.approx(0.0)
    assert anti_stud.position[1] == pytest.approx(24.0)


def test_transformed_instance_geometry_is_cached(brick):
    instance = instantiate(brick, "cached", Transform.translation(20, -24, 0))
    assert instance.triangles is instance.triangles
    assert instance.bbox is instance.bbox


def test_closed_mesh_containment_is_collision_without_surface_crossing():
    outer = instantiate(_cube_definition("outer", 10), "outer")
    inner = instantiate(_cube_definition("inner", 2), "inner", Transform.translation(1, 1, 1))
    assert check_collision(outer, inner) is Relation.COLLISION
