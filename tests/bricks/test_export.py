import json
import pytest
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import BrickExportBundle, BrickExportFidelityIssue, create_export_bundle, export_bundle_json
from brickhouse.building.models import Appearance, AppearanceSection, Facade


def _model():
    return BrickModel(building_id="house",volume_id="main",width_studs=10,depth_studs=8,height_plates=12,parts=[BrickModelPart(placement_id="wall-000001",part_id="BRICK_1X4",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade=Facade.FRONT),BrickModelPart(placement_id="roof-000001",part_id="BRICK_SLOPED_45_2X4",category="roof_tile",component="roof",x_studs=0,y_studs=1,z_plates=9,rotation_quarter_turns=0,roof_side="negative")])

def test_create_export_bundle_and_round_trip():
    m=_model();b=create_export_bundle(m,generate_bom(m));e=export_bundle_json(b);assert BrickExportBundle.model_validate_json(e)==b;assert json.loads(e)["schema_version"]=="0.1"
def test_export_preserves_architectural_appearance():
    m=_model();appearance=Appearance(walls=AppearanceSection(color="off_white"),roof=AppearanceSection(color="dark_gray"),frames=AppearanceSection(color="dark_brown"));b=create_export_bundle(m,generate_bom(m),appearance=appearance);payload=json.loads(export_bundle_json(b));assert payload["appearance"]["roof"]["color"]=="dark_gray";assert BrickExportBundle.model_validate(payload).appearance==appearance
def test_export_is_deterministic():
    m=_model();b=create_export_bundle(m,generate_bom(m));assert export_bundle_json(b)==export_bundle_json(b)
def test_rejects_mismatched_bom_total():
    m=_model();b=generate_bom(m).model_copy(update={"total_parts":99})
    with pytest.raises(ValueError,match="total_parts"):create_export_bundle(m,b)
def test_rejects_mismatched_building_id():
    m=_model();b=generate_bom(m).model_copy(update={"building_id":"other"})
    with pytest.raises(ValueError,match="building_id"):create_export_bundle(m,b)


def _colored_model():
    return BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=10,
        depth_studs=8,
        height_plates=12,
        parts=[
            BrickModelPart(
                placement_id="trim-1",
                part_id="BRICK_1X1",
                category="masonry",
                component="facade_detail",
                x_studs=1,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
                opening_id="w1",
                trim_role="left_jamb",
                semantic_color="slightly darker beige",
            ),
            BrickModelPart(
                placement_id="trim-2",
                part_id="BRICK_1X1",
                category="masonry",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
                opening_id="w1",
                trim_role="right_jamb",
                semantic_color="slightly darker beige",
            ),
        ],
    )


def test_semantic_color_adds_non_blocking_unvalidated_lego_availability_issue():
    model = _colored_model()
    bundle = create_export_bundle(model, generate_bom(model))

    issues = [issue for issue in bundle.fidelity_issues if issue.code == "lego_color_availability_unvalidated"]
    assert len(issues) == 1
    assert issues[0].severity == "info"
    assert "slightly darker beige" in issues[0].message
    assert "physically available" in issues[0].message


def test_color_availability_issue_is_deduplicated_by_category_and_semantic_color():
    model = _colored_model()
    bundle = create_export_bundle(model, generate_bom(model))

    assert sum(issue.code == "lego_color_availability_unvalidated" for issue in bundle.fidelity_issues) == 1


def test_existing_fidelity_issues_survive_automatic_color_issue_generation():
    model = _colored_model()
    existing = BrickExportFidelityIssue(
        code="existing_warning",
        severity="warning",
        message="Existing architectural warning.",
        object_id="w1",
    )
    bundle = create_export_bundle(model, generate_bom(model), fidelity_issues=[existing])

    assert bundle.fidelity_issues[0] == existing
    assert any(issue.code == "lego_color_availability_unvalidated" for issue in bundle.fidelity_issues)


def test_uncolored_models_do_not_gain_color_availability_noise():
    model = _model()
    bundle = create_export_bundle(model, generate_bom(model))

    assert all(issue.code != "lego_color_availability_unvalidated" for issue in bundle.fidelity_issues)
