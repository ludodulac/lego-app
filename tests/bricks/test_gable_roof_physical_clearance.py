from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.geometry_adapter import analyze_brick_model_geometry
from brickhouse.building.models import Facade
from lego_geometry_engine import LDrawLibrary

LDRAW_FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def _wall(placement_id: str, x: int) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X1",
        category="brick",
        component="wall",
        x_studs=x,
        y_studs=0,
        z_plates=6,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
    )


def _slope() -> BrickModelPart:
    return BrickModelPart(
        placement_id="roof",
        part_id="BRICK_SLOPED_45_2X4",
        category="roof_tile",
        component="roof",
        x_studs=0,
        y_studs=0,
        z_plates=6,
        rotation_quarter_turns=0,
        roof_side="negative",
    )


def _model(wall_x: int) -> BrickModel:
    return BrickModel(
        building_id="physical-gable",
        volume_id="main",
        width_studs=10,
        depth_studs=8,
        height_plates=12,
        parts=[_slope(), _wall("gable", wall_x)],
    )


def test_ldraw_confirms_old_course_advance_gable_position_penetrates_slope():
    report = analyze_brick_model_geometry(_model(1), LDrawLibrary(LDRAW_FIXTURE)).report
    pairs = {frozenset((item["part_a"], item["part_b"])) for item in report.collisions}
    assert frozenset(("roof", "gable")) in pairs


def test_ldraw_confirms_full_footprint_clearance_removes_penetration():
    report = analyze_brick_model_geometry(_model(2), LDrawLibrary(LDRAW_FIXTURE)).report
    pairs = {frozenset((item["part_a"], item["part_b"])) for item in report.collisions}
    assert frozenset(("roof", "gable")) not in pairs
