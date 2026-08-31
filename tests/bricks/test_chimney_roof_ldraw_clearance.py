from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.geometry_adapter import analyze_brick_model_geometry
from brickhouse.bricks.scene_chimneys import augment_brick_model_with_scene_chimneys
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene
from lego_geometry_engine import LDrawLibrary


LDRAW_FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")
SOURCE = {"kind": "inferred", "confidence": 1.0}


def _slope() -> BrickModelPart:
    return BrickModelPart(
        placement_id="roof-hit",
        part_id="BRICK_SLOPED_45_2X4",
        category="roof_tile",
        component="roof",
        x_studs=0,
        y_studs=0,
        z_plates=6,
        rotation_quarter_turns=0,
        roof_side="negative",
    )


def _manual_chimney() -> BrickModelPart:
    return BrickModelPart(
        placement_id="old-chimney",
        part_id="BRICK_1X1",
        category="brick",
        component="facade_detail",
        x_studs=1,
        y_studs=0,
        z_plates=6,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
    )


def _model(parts) -> BrickModel:
    return BrickModel(
        building_id="chimney-clearance",
        volume_id="main",
        width_studs=40,
        depth_studs=40,
        height_plates=12,
        parts=parts,
    )


def _scene() -> ArchitecturalScene:
    prop = lambda value: {"value": value, "source": SOURCE, "evidence": []}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "chimney-clearance",
            "name": "chimney clearance",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "width": prop(10.0),
                    "depth": prop(10.0),
                    "height": prop(5.0),
                    "floors": 1,
                    "source": SOURCE,
                    "evidence": [],
                }
            ],
            "chimneys": [
                {
                    "id": "c",
                    "position": {"x": 0.25, "y": 0.0, "z": 0.6},
                    "width": 0.25,
                    "depth": 0.25,
                    "height": 1.0,
                    "source": SOURCE,
                    "evidence": [],
                }
            ],
            "appearance": {},
        }
    )


def _collision_pairs(model: BrickModel) -> set[frozenset[str]]:
    report = analyze_brick_model_geometry(model, LDrawLibrary(LDRAW_FIXTURE)).report
    return {
        frozenset((item["part_a"], item["part_b"]))
        for item in report.collisions
    }


def test_ldraw_confirms_uncarved_chimney_physically_penetrates_roof_slope() -> None:
    pairs = _collision_pairs(_model([_slope(), _manual_chimney()]))
    assert frozenset(("roof-hit", "old-chimney")) in pairs


def test_ldraw_confirms_metric_chimney_carving_removes_roof_collision() -> None:
    augmented = augment_brick_model_with_scene_chimneys(
        _model([_slope()]),
        _scene(),
        front_width_studs=40,
    )
    assert "roof-hit" not in {part.placement_id for part in augmented.parts}
    assert not _collision_pairs(augmented)
