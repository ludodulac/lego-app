import json

import pytest

from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import BrickExportBundle, create_export_bundle, export_bundle_json
from brickhouse.building.models import Facade


def _model():
    return BrickModel(
        building_id="house", volume_id="main", width_studs=10, depth_studs=8, height_plates=12,
        parts=[
            BrickModelPart(placement_id="wall-000001", part_id="BRICK_1X4", category="brick", component="wall", x_studs=0, y_studs=0, z_plates=0, rotation_quarter_turns=1, facade=Facade.FRONT),
            BrickModelPart(placement_id="roof-000001", part_id="ROOF_SLOPE_2X4", category="roof_tile", component="roof", x_studs=0, y_studs=1, z_plates=9, rotation_quarter_turns=0, roof_side="negative"),
        ],
    )


def test_create_export_bundle_and_round_trip():
    model=_model(); bundle=create_export_bundle(model,generate_bom(model)); encoded=export_bundle_json(bundle); restored=BrickExportBundle.model_validate_json(encoded)
    assert restored==bundle
    assert json.loads(encoded)["schema_version"]=="0.1"


def test_export_is_deterministic():
    model=_model(); bundle=create_export_bundle(model,generate_bom(model)); assert export_bundle_json(bundle)==export_bundle_json(bundle)


def test_rejects_mismatched_bom_total():
    model=_model(); bom=generate_bom(model).model_copy(update={"total_parts":99})
    with pytest.raises(ValueError,match="total_parts"): create_export_bundle(model,bom)


def test_rejects_mismatched_building_id():
    model=_model(); bom=generate_bom(model).model_copy(update={"building_id":"other"})
    with pytest.raises(ValueError,match="building_id"): create_export_bundle(model,bom)
