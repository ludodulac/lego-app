from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import BrickExportFidelitySummary, create_export_bundle
from brickhouse.building.models import Facade


def _model() -> BrickModel:
    return BrickModel(
        building_id="generic-building",
        volume_id="main",
        width_studs=8,
        depth_studs=6,
        height_plates=9,
        parts=[
            BrickModelPart(
                placement_id="wall-1",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            )
        ],
    )


def test_new_export_summarizes_empty_fidelity_issue_list() -> None:
    model = _model()
    bundle = create_export_bundle(model, generate_bom(model))

    assert bundle.fidelity_summary == BrickExportFidelitySummary(
        info_count=0,
        warning_count=0,
        blocker_count=0,
        has_blockers=False,
    )
