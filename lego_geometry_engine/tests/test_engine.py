from pathlib import Path
import pytest

from lego_geometry_engine import LDrawLibrary, Relation, Transform, analyze_assembly, check_collision, instantiate

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
