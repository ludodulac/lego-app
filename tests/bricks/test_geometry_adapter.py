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


def _roof_part(
    placement_id: str,
    *,
    side: str,
    x: int = 0,
    y: int = 0,
    z: int = 0,
    turns: int = 0,
    part_id: str = "BRICK_SLOPED_45_2X4",
) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id=part_id,
        category="roof_tile",
        component="roof",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=turns,
        roof_side=side,
    )


def _box_definition(part_id: str, minimum, maximum, description: str = "") -> PartDefinition:
    x0, y0, z0 = minimum
    x1, y1, z1 = maximum
    p000 = (x0, y0, z0)
    p001 = (x0, y0, z1)
    p010 = (x0, y1, z0)
    p011 = (x0, y1, z1)
    p100 = (x1, y0, z0)
    p101 = (x1, y0, z1)
    p110 = (x1, y1, z0)
    p111 = (x1, y1, z1)
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
        bbox=AABB(minimum, maximum),
        description=description,
    )


def _cube_definition(part_id: str = "3005.dat") -> PartDefinition:
    return _box_definition(
        part_id,
        (-10.0, 0.0, -10.0),
        (10.0, 24.0, 10.0),
        "Brick 1 x 1",
    )


def _slope_2x4_definition() -> PartDefinition:
    # Horizontal bounds match the official 3037 geometry: four studs along
    # local X and two studs along local Z, with the Z origin offset by -10 LDU.
    return _box_definition(
        "3037.dat",
        (-40.0, 0.0, -30.0),
        (40.0, 24.0, 10.0),
        "Slope Brick 45 2 x 4",
    )


class FakeLibrary:
    def __init__(self):
        self.loaded = []
        self.brick_definition = _cube_definition()
        self.slope_definition = _slope_2x4_definition()

    def load_part(self, part_id: str):
        self.loaded.append(part_id)
        if part_id == "3037":
            return self.slope_definition
        return self.brick_definition


def test_mapping_covers_the_m0_standard_brick_catalog_and_verified_roof_subset():
    expected = {brick.id for brick in create_m0_brick_catalog().bricks}
    assert expected.issubset(CANONICAL_LDRAW_PARTS)
    assert CANONICAL_LDRAW_PARTS["BRICK_1X1"].ldraw_id == "3005"
    assert CANONICAL_LDRAW_PARTS["BRICK_2X4"].ldraw_id == "3001"
    assert CANONICAL_LDRAW_PARTS["BRICK_SLOPED_45_2X4"].ldraw_id == "3037"
    assert CANONICAL_LDRAW_PARTS["BRICK_SLOPED_45_2X3"].ldraw_id == "3038"
    assert CANONICAL_LDRAW_PARTS["BRICK_SLOPED_45_2X2"].ldraw_id == "3039"
    assert CANONICAL_LDRAW_PARTS["BRICK_SLOPED_45_2X1"].ldraw_id == "3040b"


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


def test_negative_45_slope_aligns_decentered_ldraw_bbox_to_brickmodel_footprint():
    library = FakeLibrary()
    instance = brick_model_part_to_instance(
        _roof_part("roof-neg", side="negative", x=2, y=5, z=12, turns=0),
        library,
    )
    assert library.loaded == ["3037"]
    assert instance.bbox.minimum[0] == pytest.approx(40.0)
    assert instance.bbox.maximum[0] == pytest.approx(80.0)
    assert instance.bbox.minimum[2] == pytest.approx(100.0)
    assert instance.bbox.maximum[2] == pytest.approx(180.0)
    assert instance.bbox.maximum[1] == pytest.approx(-96.0)
    # Negative side rises inward along +grid X: local +Z maps to world +X.
    assert instance.transform.vector((0.0, 0.0, 1.0))[0] == pytest.approx(1.0)


def test_positive_45_slope_reverses_rise_without_moving_footprint():
    library = FakeLibrary()
    instance = brick_model_part_to_instance(
        _roof_part("roof-pos", side="positive", x=7, y=1, z=9, turns=0),
        library,
    )
    assert instance.bbox.minimum[0] == pytest.approx(140.0)
    assert instance.bbox.maximum[0] == pytest.approx(180.0)
    assert instance.bbox.minimum[2] == pytest.approx(20.0)
    assert instance.bbox.maximum[2] == pytest.approx(100.0)
    assert instance.bbox.maximum[1] == pytest.approx(-72.0)
    assert instance.transform.vector((0.0, 0.0, 1.0))[0] == pytest.approx(-1.0)


def test_rotated_45_slope_aligns_when_ridge_runs_along_width_axis():
    library = FakeLibrary()
    instance = brick_model_part_to_instance(
        _roof_part("roof-rot", side="negative", x=3, y=4, z=6, turns=1),
        library,
    )
    assert instance.bbox.minimum[0] == pytest.approx(60.0)
    assert instance.bbox.maximum[0] == pytest.approx(140.0)
    assert instance.bbox.minimum[2] == pytest.approx(80.0)
    assert instance.bbox.maximum[2] == pytest.approx(120.0)
    assert instance.transform.vector((0.0, 0.0, 1.0))[2] == pytest.approx(1.0)


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
