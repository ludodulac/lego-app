import pytest
from pydantic import ValidationError

from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import (
    BrickExportBundle,
    BrickExportCapabilitySummary,
    BrickExportFidelityIssue,
    MechanicalVerificationSummary,
    create_export_bundle,
    export_bundle_json,
)


def _model() -> BrickModel:
    return BrickModel(
        building_id="capability-house",
        volume_id="main",
        width_studs=1,
        depth_studs=1,
        height_plates=3,
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
                facade="front",
            )
        ],
    )


def _full_bundle(*, fidelity_issues=None, mechanical_verification=None):
    model = _model()
    return create_export_bundle(
        model,
        generate_bom(model),
        generate_assembly_plan(model),
        fidelity_issues=fidelity_issues,
        mechanical_verification=mechanical_verification,
    )


def test_full_export_reports_artifact_contracts_without_mechanical_overclaim():
    bundle = _full_bundle()
    summary = bundle.capability_summary

    assert summary is not None
    assert summary.render_artifact == "available"
    assert summary.bom == "contract_verified"
    assert summary.assembly_plan == "contract_verified"
    assert summary.instruction_plan == "contract_verified"
    assert summary.bag_plan == "contract_verified"
    assert summary.fidelity_level == "clear"
    assert summary.mechanical_verification.state == "not_claimed"
    assert summary.mechanical_verification.validator_id is None
    assert summary.mechanical_verification.scopes == []


def test_export_without_assembly_does_not_claim_downstream_plans():
    model = _model()
    bundle = create_export_bundle(model, generate_bom(model))
    summary = bundle.capability_summary

    assert summary is not None
    assert summary.bom == "contract_verified"
    assert summary.assembly_plan == "not_available"
    assert summary.instruction_plan == "not_available"
    assert summary.bag_plan == "not_available"
    assert summary.mechanical_verification.state == "not_claimed"


def test_historical_schema_01_bundle_can_omit_additive_capability_summary():
    model = _model()
    bundle = BrickExportBundle(
        building_id=model.building_id,
        volume_id=model.volume_id,
        brick_model=model,
        bom=generate_bom(model),
    )
    assert bundle.schema_version == "0.1"
    assert bundle.capability_summary is None


def test_warning_only_fidelity_is_degraded_but_not_blocked():
    bundle = _full_bundle(fidelity_issues=[
        BrickExportFidelityIssue(
            code="example_warning",
            severity="warning",
            message="A represented detail remains approximate.",
        )
    ])
    assert bundle.capability_summary is not None
    assert bundle.capability_summary.fidelity_level == "degraded"


def test_blocker_fidelity_is_explicitly_blocked():
    bundle = _full_bundle(fidelity_issues=[
        BrickExportFidelityIssue(
            code="example_blocker",
            severity="blocker",
            message="A required architectural element is not faithfully representable.",
        )
    ])
    assert bundle.capability_summary is not None
    assert bundle.capability_summary.fidelity_level == "blocked"


def test_info_only_fidelity_does_not_promote_or_degrade_guarantees():
    bundle = _full_bundle(fidelity_issues=[
        BrickExportFidelityIssue(
            code="example_info",
            severity="info",
            message="A traceable representation note.",
        )
    ])
    assert bundle.capability_summary is not None
    assert bundle.capability_summary.fidelity_level == "clear"
    assert bundle.capability_summary.mechanical_verification.state == "not_claimed"


def test_scoped_mechanical_claim_requires_named_validator_and_scope():
    with pytest.raises(ValidationError):
        MechanicalVerificationSummary(state="verified_in_declared_scope")

    claim = MechanicalVerificationSummary(
        state="verified_in_declared_scope",
        validator_id="example-validator-v1",
        scopes=["collision/contact subset"],
    )
    bundle = _full_bundle(mechanical_verification=claim)
    assert bundle.capability_summary is not None
    assert bundle.capability_summary.mechanical_verification == claim


def test_capability_summary_cannot_disagree_with_bundle_artifacts():
    model = _model()
    bom = generate_bom(model)
    with pytest.raises(ValidationError):
        # An old/manual bundle may omit the additive summary entirely, but if one
        # is supplied it must describe the actual artifacts rather than a wish.
        BrickExportBundle(
            building_id=model.building_id,
            volume_id=model.volume_id,
            brick_model=model,
            bom=bom,
            capability_summary=BrickExportCapabilitySummary(
                bom="contract_verified",
                assembly_plan="contract_verified",
                instruction_plan="not_available",
                bag_plan="not_available",
                fidelity_level="clear",
            ),
        )


def test_capability_summary_is_deterministic_in_export_json():
    first = export_bundle_json(_full_bundle())
    second = export_bundle_json(_full_bundle())
    assert first == second
