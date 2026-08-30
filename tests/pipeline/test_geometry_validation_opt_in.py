from pathlib import Path

from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.pipeline import _geometry_fidelity_issues


LDRAW_FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def _part(placement_id: str, *, x: int = 0) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X1",
        category="brick",
        component="wall",
        x_studs=x,
        y_studs=0,
        z_plates=0,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
    )


def _model(parts) -> BrickModel:
    return BrickModel(
        building_id="geometry-opt-in",
        volume_id="main",
        width_studs=4,
        depth_studs=1,
        height_plates=3,
        parts=parts,
    )


def test_geometry_validation_is_disabled_without_explicit_ldraw_root():
    # This intentionally overlaps two bricks. The default production path must
    # remain unchanged and must not require an LDraw installation.
    assert _geometry_fidelity_issues(_model([_part("a"), _part("b")]), None) == []


def test_opt_in_geometry_validation_surfaces_collision_as_blocker():
    issues = _geometry_fidelity_issues(_model([_part("a"), _part("b")]), LDRAW_FIXTURE)
    collision = next(issue for issue in issues if issue.code == "lego_geometry_collision")
    assert collision.severity == "blocker"
    assert "'a'" in collision.message and "'b'" in collision.message


def test_opt_in_geometry_validation_accepts_separated_ground_parts():
    issues = _geometry_fidelity_issues(_model([_part("a"), _part("b", x=2)]), LDRAW_FIXTURE)
    assert not [issue for issue in issues if issue.code == "lego_geometry_collision"]
