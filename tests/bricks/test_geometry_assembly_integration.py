from pathlib import Path

from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.geometry_adapter import analyze_brick_model_geometry
from lego_geometry_engine import LDrawLibrary

LDRAW_FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def _part(placement_id: str, part_id: str, *, x: int, y: int, z: int, roof_side=None, category="brick") -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id=part_id,
        category=category,
        component="roof" if roof_side else "wall",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
        roof_side=roof_side,
    )


def _model(parts) -> BrickModel:
    return BrickModel(
        building_id="mixed-geometry",
        volume_id="main",
        width_studs=12,
        depth_studs=8,
        height_plates=18,
        parts=parts,
    )


def test_mixed_brick_slope_window_assembly_has_no_false_collisions():
    parts = [
        _part("ground", "BRICK_1X1", x=0, y=0, z=0),
        _part("slope", "BRICK_SLOPED_45_2X4", x=4, y=0, z=3, roof_side="negative", category="roof_slope"),
        _part("frame", "WINDOW_1X2X2_60592", x=8, y=0, z=0, category="window_frame"),
        _part("pane", "GLASS_FOR_WINDOW_1X2X2_60601", x=8, y=0, z=0, category="window_pane"),
    ]
    result = analyze_brick_model_geometry(_model(parts), LDrawLibrary(LDRAW_FIXTURE))
    assert result.complete
    assert not result.report.collisions
    assert set(result.mapped_placements) == {"ground", "slope", "frame", "pane"}


def test_mixed_assembly_reports_only_deliberate_brick_collision_ids():
    parts = [
        _part("brick-a", "BRICK_1X1", x=0, y=0, z=0),
        _part("brick-b", "BRICK_1X1", x=0, y=0, z=0),
        _part("slope", "BRICK_SLOPED_45_2X4", x=4, y=0, z=3, roof_side="negative", category="roof_slope"),
        _part("frame", "WINDOW_1X2X2_60592", x=8, y=0, z=0, category="window_frame"),
        _part("pane", "GLASS_FOR_WINDOW_1X2X2_60601", x=8, y=0, z=0, category="window_pane"),
    ]
    report = analyze_brick_model_geometry(_model(parts), LDrawLibrary(LDRAW_FIXTURE)).report
    collision_pairs = {frozenset((item["part_a"], item["part_b"])) for item in report.collisions}
    assert collision_pairs == {frozenset(("brick-a", "brick-b"))}
