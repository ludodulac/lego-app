import copy

import pytest

from brickhouse.bricks.building_layout import BuildingBrickShell, BuildingWallLayout
from brickhouse.bricks.placement import generate_simple_wall_layout
from brickhouse.bricks.roof import (
    create_m0_roof_catalog,
    generate_spatial_gable_roof,
    select_roof_slope_family,
    validate_roof_support,
)
from brickhouse.bricks.scaling import WallGridSpec
from brickhouse.building.models import Facade, RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, Point3D, RoofPlaneGeometry


def _wall_record(facade, width, height=6):
    grid = WallGridSpec(
        wall_id=f"v:{facade.value}",
        width_studs=width,
        height_bricks=height,
        studs_per_meter=1.0,
        courses_per_meter=1.0,
        openings=[],
    )
    return BuildingWallLayout(
        wall_id=grid.wall_id,
        facade=facade,
        grid=grid,
        layout=generate_simple_wall_layout(width, height),
    )


def _shell(width=10, depth=8, height=6):
    return BuildingBrickShell(
        building_id="b",
        volume_id="v",
        reference_width_studs=width,
        studs_per_meter=1.0,
        walls=[
            _wall_record(Facade.FRONT, width, height),
            _wall_record(Facade.REAR, width, height),
            _wall_record(Facade.LEFT, depth, height),
            _wall_record(Facade.RIGHT, depth, height),
        ],
    )


def _geometry(direction, roof_rise=3, *, width=10, depth=8):
    ridge_z = 6 + roof_rise
    if direction is RidgeDirection.DEPTH:
        half = width / 2
        negative = [
            Point3D(x=0, y=0, z=6),
            Point3D(x=half, y=0, z=ridge_z),
            Point3D(x=half, y=depth, z=ridge_z),
            Point3D(x=0, y=depth, z=6),
        ]
        positive = [
            Point3D(x=half, y=0, z=ridge_z),
            Point3D(x=width, y=0, z=6),
            Point3D(x=width, y=depth, z=6),
            Point3D(x=half, y=depth, z=ridge_z),
        ]
    else:
        half = depth / 2
        negative = [
            Point3D(x=0, y=0, z=6),
            Point3D(x=width, y=0, z=6),
            Point3D(x=width, y=half, z=ridge_z),
            Point3D(x=0, y=half, z=ridge_z),
        ]
        positive = [
            Point3D(x=0, y=half, z=ridge_z),
            Point3D(x=width, y=half, z=ridge_z),
            Point3D(x=width, y=depth, z=6),
            Point3D(x=0, y=depth, z=6),
        ]
    return BuildingGeometry(
        building_id="b",
        walls=[],
        roof_planes=[
            RoofPlaneGeometry(
                id="r:n", roof_id="r", volume_id="v", roof_type=RoofType.GABLE,
                side="negative", ridge_direction=direction, corners=negative,
            ),
            RoofPlaneGeometry(
                id="r:p", roof_id="r", volume_id="v", roof_type=RoofType.GABLE,
                side="positive", ridge_direction=direction, corners=positive,
            ),
        ],
    )


def test_roof_catalog_contains_only_explicitly_modeled_slope_families():
    catalog = create_m0_roof_catalog()
    assert catalog.get("BRICK_SLOPED_18_4X2").slope_family == "18"
    assert catalog.get("BRICK_SLOPED_33_3X6").slope_family == "33"
    assert catalog.get("BRICK_SLOPED_45_2X4").slope_family == "45"
    assert catalog.get("TILE_2X4").category == "ridge_tile"


def test_closest_slope_family_selection_is_deterministic():
    assert select_roof_slope_family(22).id == "18"
    assert select_roof_slope_family(35).id == "33"
    assert select_roof_slope_family(44).id == "45"
    assert select_roof_slope_family(39).id == "33"
    with pytest.raises(ValueError, match="positive"):
        select_roof_slope_family(0)


@pytest.mark.parametrize("direction", [RidgeDirection.DEPTH, RidgeDirection.WIDTH])
def test_gable_roof_supports_both_ridge_directions_with_33_family(direction):
    shell = _shell()
    roof = generate_spatial_gable_roof(_geometry(direction), shell)
    assert roof.ridge_direction is direction
    assert any(part.part_id.startswith("BRICK_SLOPED_33_") for part in roof.placements)
    validate_roof_support(roof, shell)


def test_low_pitch_target_uses_18_family_instead_of_steep_33_family():
    roof = generate_spatial_gable_roof(
        _geometry(RidgeDirection.DEPTH, roof_rise=2),
        _shell(),
    )
    assert any(part.part_id == "BRICK_SLOPED_18_4X2" for part in roof.placements)
    assert not any(part.part_id.startswith("BRICK_SLOPED_33_") for part in roof.placements)


def test_45_degree_target_uses_45_family():
    roof = generate_spatial_gable_roof(
        _geometry(RidgeDirection.DEPTH, roof_rise=5),
        _shell(),
    )
    assert any(part.part_id.startswith("BRICK_SLOPED_45_") for part in roof.placements)
    assert not any(part.part_id.startswith("BRICK_SLOPED_33_") for part in roof.placements)


def test_each_33_degree_course_uses_two_stud_advance_and_three_plate_rise():
    roof = generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), _shell())
    courses = {}
    for part in roof.placements:
        if part.side == "negative":
            courses.setdefault(part.x_studs, part.z_plates)
    axes = sorted(courses)
    assert all(b - a == 2 for a, b in zip(axes, axes[1:]))
    levels = [courses[axis] for axis in axes]
    assert all(b - a == 3 for a, b in zip(levels, levels[1:]))


def test_each_18_degree_course_uses_three_stud_advance_and_three_plate_rise():
    roof = generate_spatial_gable_roof(
        _geometry(RidgeDirection.DEPTH, roof_rise=2),
        _shell(),
    )
    courses = {}
    for part in roof.placements:
        if part.side == "negative":
            courses.setdefault(part.x_studs, part.z_plates)
    axes = sorted(courses)
    assert all(b - a == 3 for a, b in zip(axes, axes[1:]))
    levels = [courses[axis] for axis in axes]
    assert all(b - a == 3 for a, b in zip(levels, levels[1:]))


def test_eave_courses_are_anchored_on_wall_top():
    roof = generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), _shell())
    negative = min(
        (part for part in roof.placements if part.side == "negative"),
        key=lambda part: part.x_studs,
    )
    positive = max(
        (part for part in roof.placements if part.side == "positive"),
        key=lambda part: part.x_studs,
    )
    assert (negative.x_studs, negative.z_plates) == (0, 18)
    assert (positive.x_studs, positive.z_plates) == (7, 18)


def test_no_duplicate_spatial_slope_placements_at_center():
    roof = generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), _shell())
    keys = [
        (
            part.part_id,
            part.x_studs,
            part.y_studs,
            part.z_plates,
            part.rotation_quarter_turns,
        )
        for part in roof.placements
        if part.side != "ridge"
    ]
    assert len(keys) == len(set(keys))


def test_validator_rejects_broken_course_advance():
    shell = _shell()
    broken = copy.deepcopy(generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), shell))
    for part in broken.placements:
        if part.side == "negative" and part.x_studs == 2:
            part.x_studs += 1
    with pytest.raises(ValueError, match="course advance|floating roof course"):
        validate_roof_support(broken, shell)


def test_validator_rejects_wrong_slope_rise():
    shell = _shell()
    broken = copy.deepcopy(generate_spatial_gable_roof(_geometry(RidgeDirection.DEPTH), shell))
    for part in broken.placements:
        if part.side == "negative" and part.x_studs == 2:
            part.z_plates += 1
    with pytest.raises(ValueError, match="selected slope connection rise"):
        validate_roof_support(broken, shell)


def test_odd_cross_roof_span_is_supported_with_one_stud_positive_eave_extension():
    shell = _shell(width=9)
    roof = generate_spatial_gable_roof(
        _geometry(RidgeDirection.DEPTH, width=9),
        shell,
    )
    assert roof.placements
    validate_roof_support(roof, shell)


def test_generation_is_deterministic():
    assert generate_spatial_gable_roof(
        _geometry(RidgeDirection.WIDTH), _shell()
    ).model_dump(mode="json") == generate_spatial_gable_roof(
        _geometry(RidgeDirection.WIDTH), _shell()
    ).model_dump(mode="json")


def test_non_gable_or_missing_planes_are_rejected():
    with pytest.raises(ValueError, match="exactly two"):
        generate_spatial_gable_roof(
            BuildingGeometry(building_id="b", walls=[], roof_planes=[]),
            _shell(),
        )
