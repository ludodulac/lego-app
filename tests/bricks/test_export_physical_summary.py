import pytest

from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.building_layout import BuildingDiscretizationQuality
from brickhouse.bricks.export import create_export_bundle
from brickhouse.building.models import Facade


def _model():
    return BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=48,
        depth_studs=38,
        height_plates=72,
        parts=[BrickModelPart(
            placement_id="wall-1",
            part_id="BRICK_1X2",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade=Facade.FRONT,
        )],
    )


def test_export_reports_physical_lego_dimensions_and_scale_from_discretization():
    model = _model()
    quality = BuildingDiscretizationQuality(
        volume_id="main",
        studs_per_meter=4.8,
        walls=[],
        mean_absolute_error_m=0,
        worst_absolute_error_m=0,
    )
    bundle = create_export_bundle(model, generate_bom(model), discretization_quality=[quality])
    physical = bundle.metadata.physical_model

    assert physical is not None
    assert physical.width_mm == 384
    assert physical.depth_mm == 304
    assert physical.height_mm == pytest.approx(230.4)
    assert physical.approximate_scale_denominator == pytest.approx(26.0416667)


def test_export_keeps_physical_dimensions_but_not_fake_scale_without_metric_report():
    model = _model()
    bundle = create_export_bundle(model, generate_bom(model))

    assert bundle.metadata.physical_model.width_mm == 384
    assert bundle.metadata.physical_model.approximate_scale_denominator is None
