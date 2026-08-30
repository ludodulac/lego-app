import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.geometry_adapter import (
    CANONICAL_LDRAW_PARTS,
    UnmappedCanonicalPartError,
    analyze_brick_model_geometry,
    brick_model_part_to_instance,
    brick_model_part_transform,
)
from brickhouse.building.models import Facade
from lego_geometry_engine import AABB, PartDefinition, Relation, check_collision


def _part(
    placement_id: str,
    part_id: str = "BRICK_1X1",
    *,
    x: int = 0,
    y: int = 0,
    z: int = 0,
    turns: int = 0,
) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id=part_id,
        category="brick",
        component="wall",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=turns,
        facade=Facade.FRONT,
    )


def _cube_definition(part_id: str = "3005.dat") -> PartDefinition:
    p000 = (-10.0, 0.0, -10.0)
    p001 = (-10.0, 0.0, 10.0)
    p010 = (-10.0, 24.0, -10.0)
    p011 = (-10.0, 24.0, 10.0)
    p100 = (10.0, 0.0, -10.0)
    p101 = (10.0, 0.0, 10.0)
    p110 = (10.0, 24.0, -10.0)
    p111 = (10.0, 24.0, 10.0)
    triangles = (
        (p000, p100, p101), (p000, p101, p001),
        (p010, p011, p111), (p010, p111, p110),
        (p000, p010, p110), (p000, p110, p100),
        (p001, p101, p111), (p001, p111, p011),
        (p000, p001, p011), (p000, p011, p010),
        (p100, p110, p111), (p100, p111, p101),
    )
    return PartDefinition(
        part_id=part_id,
        triangles=triangles,
        bbox=AABB((-10.0, 0.0, -10.0), (10.0, 24.0, 10.0)),
        description="Brick 1 x 1",
    )


class FakeLibrary:
    def __init__(self):
        self.loaded = []
        self.definition = _cube_definition()

    def load_part(self, part_id: str):
        self.loaded.append(part_id)
        return self.definition


def test_mapping_covers_exactly_the_m0_standard_brick_catalog():
    expected = {brick.id for brick in create_m0_brick_catalog().bricks}
    assert set(CANONICAL_LDRAW_PARTS) == expected
    assert CANONICAL_LDRAW_PARTS["BRICK_1X1"].ldraw_id == "3005"
    assert CANONICAL_LDRAW_PARTS["BRICK_2X4"].ldraw_id == "3001"


def test_grid_coordinates_convert_to_ldraw_center_and_negative_y_up():
    part = _part("p", "BRICK_1X2", x=2, y=3, z=6)
    transform = brick_model_part_transform(part, CANONICAL_LDRAW_PARTS[part.part_id])
    assert transform.matrix[0][3] == 50.0
    assert transform.matrix[1][3] == -72.0
    assert transform.matrix[2][3] == 80.0


def test_quarter_turn_uses_rotated_footprint_center():
    part = _part("p", "BRICK_1X4", x=2, y=3, turns=1)
    transform = brick_model_part_transform(part, CANONICAL_LDRAW_PARTS[part.part_id])
    assert transform.matrix[0][3] == 80.0
    assert transform.matrix[2][3] == 70.0
    assert transform.matrix[0][:3] == (0.0, 0.0, 1.0)
    assert transform.matrix[2][:3] == (-1.0, 0.0, 0.0)


def test_adapter_preserves_placement_id_and_uses_verified_ldraw_id():
    library = FakeLibrary()
    instance = brick_model_part_to_instance(_part("wall-000001"), library)
    assert library.loaded == ["3005"]
    assert instance.instance_id == "wall-000001"


def test_two_canonical_bricks_on_consecutive_courses_contact_without_collision():
    library = FakeLibrary()
    lower = brick_model_part_to_instance(_part("lower", z=0), library)
    upper = brick_model_part_to_instance(_part("upper", z=3), library)
    assert check_collision(lower, upper) is Relation.CONTACT


def test_strict_mode_rejects_unmapped_parts_instead_of_guessing():
    model = BrickModel(
        building_id="b",
        volume_id="v",
        width_studs=2,
        depth_studs=2,
        height_plates=3,
        parts=[_part("unknown", "UNVERIFIED_PART")],
    )
    with pytest.raises(UnmappedCanonicalPartError):
        analyze_brick_model_geometry(model, FakeLibrary())


def test_partial_mode_is_explicitly_incomplete_and_never_valid():
    model = BrickModel(
        building_id="b",
        volume_id="v",
        width_studs=2,
        depth_studs=2,
        height_plates=3,
        parts=[_part("mapped"), _part("unknown", "UNVERIFIED_PART", x=1)],
    )
    result = analyze_brick_model_geometry(model, FakeLibrary(), strict=False)
    assert result.mapped_placements == ("mapped",)
    assert result.unmapped_placements == ("unknown",)
    assert result.complete is False
    assert result.valid is False
