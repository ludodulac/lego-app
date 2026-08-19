import pytest
from pydantic import ValidationError

from brickhouse.bricks import BrickCatalog, BrickDefinition, create_m0_brick_catalog


def test_m0_catalog_contains_expected_12_types():
    catalog = create_m0_brick_catalog()
    assert len(catalog.bricks) == 12
    assert [b.id for b in catalog.bricks] == [
        "BRICK_1X1", "BRICK_1X2", "BRICK_1X3", "BRICK_1X4", "BRICK_1X6", "BRICK_1X8",
        "BRICK_2X2", "BRICK_2X3", "BRICK_2X4", "BRICK_2X6", "BRICK_2X8", "BRICK_2X10",
    ]


def test_standard_brick_dimensions_and_height():
    brick = create_m0_brick_catalog().get("BRICK_2X4")
    assert (brick.width_studs, brick.length_studs, brick.height_plates) == (2, 4, 3)


def test_stud_count_is_footprint_area():
    assert create_m0_brick_catalog().get("BRICK_2X4").stud_count == 8


def test_grid_volume_is_integer_and_deterministic():
    assert create_m0_brick_catalog().get("BRICK_2X4").volume_grid_units == 24


def test_rotation_zero_preserves_footprint():
    brick = create_m0_brick_catalog().get("BRICK_1X4")
    assert brick.footprint(0) == (1, 4)
    assert brick.footprint(4) == (1, 4)


def test_rotation_quarter_turn_swaps_footprint():
    brick = create_m0_brick_catalog().get("BRICK_1X4")
    assert brick.footprint(1) == (4, 1)
    assert brick.footprint(3) == (4, 1)


def test_square_brick_rotation_is_unchanged():
    brick = create_m0_brick_catalog().get("BRICK_2X2")
    assert brick.footprint(1) == (2, 2)


def test_lookup_unknown_id_raises_key_error():
    with pytest.raises(KeyError):
        create_m0_brick_catalog().get("UNKNOWN")


def test_duplicate_ids_are_rejected():
    brick = BrickDefinition(id="BRICK_1X1", width_studs=1, length_studs=1)
    with pytest.raises(ValidationError):
        BrickCatalog(catalog_id="bad", bricks=[brick, brick])


@pytest.mark.parametrize("field", ["width_studs", "length_studs", "height_plates"])
def test_non_positive_dimensions_are_rejected(field):
    data = dict(id="BAD", width_studs=1, length_studs=1, height_plates=3)
    data[field] = 0
    with pytest.raises(ValidationError):
        BrickDefinition(**data)


def test_serialization_is_deterministic():
    first = create_m0_brick_catalog().model_dump_json()
    second = create_m0_brick_catalog().model_dump_json()
    assert first == second
