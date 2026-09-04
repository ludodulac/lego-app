import pytest

from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import (
    BrickExportBundle,
    BrickExportFidelityIssue,
    BrickExportFidelitySummary,
    create_export_bundle,
)
from brickhouse.building.models import Facade


def _model(*, semantic_color: str | None = None) -> BrickModel:
    return BrickModel(
        building_id="generic-building",
        volume_id="main",
        width_studs=8,
        depth_studs=6,
        height_plates=9,
        parts=[
            BrickModelPart(
                placement_id="detail-1" if semantic_color is not None else "wall-1",
                part_id="BRICK_1X1",
                category="brick",
                component="facade_detail" if semantic_color is not None else "wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
                semantic_color=semantic_color,
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


def test_new_export_summarizes_final_mixed_severity_list() -> None:
    model = _model()
    issues = [
        BrickExportFidelityIssue(code="i", severity="info", message="Info."),
        BrickExportFidelityIssue(code="w", severity="warning", message="Warning."),
        BrickExportFidelityIssue(code="b", severity="blocker", message="Blocker."),
    ]

    bundle = create_export_bundle(model, generate_bom(model), fidelity_issues=issues)

    assert bundle.fidelity_summary == BrickExportFidelitySummary(
        info_count=1,
        warning_count=1,
        blocker_count=1,
        has_blockers=True,
    )


def test_summary_counts_deduplicated_issues_not_raw_inputs() -> None:
    model = _model()
    duplicate = BrickExportFidelityIssue(
        code="same",
        severity="warning",
        object_id="wall-1",
        message="Same issue.",
    )

    bundle = create_export_bundle(
        model,
        generate_bom(model),
        fidelity_issues=[duplicate, duplicate.model_copy()],
    )

    assert len(bundle.fidelity_issues) == 1
    assert bundle.fidelity_summary.warning_count == 1


def test_summary_includes_automatically_generated_semantic_color_issue() -> None:
    model = _model(semantic_color="warm beige")
    bundle = create_export_bundle(model, generate_bom(model))

    assert len(bundle.fidelity_issues) == 1
    assert bundle.fidelity_issues[0].code == "lego_color_availability_unvalidated"
    assert bundle.fidelity_summary.info_count == 1
    assert bundle.fidelity_summary.warning_count == 0
    assert bundle.fidelity_summary.blocker_count == 0
    assert bundle.fidelity_summary.has_blockers is False


def test_historical_schema_v01_bundle_without_summary_still_parses() -> None:
    model = _model()
    current = create_export_bundle(
        model,
        generate_bom(model),
        fidelity_issues=[
            BrickExportFidelityIssue(
                code="historical_blocker",
                severity="blocker",
                message="Historical diagnostic blocker.",
            )
        ],
    )
    payload = current.model_dump(mode="json")
    payload.pop("fidelity_summary")

    parsed = BrickExportBundle.model_validate(payload)

    assert parsed.schema_version == "0.1"
    assert parsed.fidelity_summary is None
    assert parsed.fidelity_issues[0].severity == "blocker"


def test_present_summary_must_match_serialized_issue_severities() -> None:
    model = _model()
    current = create_export_bundle(
        model,
        generate_bom(model),
        fidelity_issues=[
            BrickExportFidelityIssue(code="warning", severity="warning", message="Warning.")
        ],
    )
    payload = current.model_dump(mode="json")
    payload["fidelity_summary"] = {
        "info_count": 0,
        "warning_count": 0,
        "blocker_count": 0,
        "has_blockers": False,
    }

    with pytest.raises(ValueError, match="fidelity_summary"):
        BrickExportBundle.model_validate(payload)
