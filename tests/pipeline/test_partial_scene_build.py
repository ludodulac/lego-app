from pathlib import Path

import pytest

from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene_cli import load_architectural_scene, write_scene_export


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_current_brickhouse_scene_can_build_useful_core_before_roof_is_resolved() -> None:
    scene = load_architectural_scene(FIXTURE)

    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)

    assert bundle.brick_model.parts
    assert bundle.brick_model.volume_id == "volume_main"
    assert any(part.component == "wall" for part in bundle.brick_model.parts)
    assert not any(part.component == "roof" for part in bundle.brick_model.parts)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan.steps[0].phase == "Structure"
    codes = {issue.code for issue in bundle.fidelity_issues}
    assert "partial_preview_roof_omitted" in codes
    assert "partial_preview_secondary_volume_omitted" in codes
    assert "low_confidence_partial_dimension" in codes
    assert "low_confidence_partial_opening_geometry" in codes
    omitted = [
        issue for issue in bundle.fidelity_issues
        if issue.code == "partial_preview_secondary_volume_omitted"
    ]
    assert {issue.object_id for issue in omitted} == {"lower_exterior_volume"}


def test_user_provided_front_width_is_not_reported_as_low_confidence() -> None:
    scene = load_architectural_scene(FIXTURE)

    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)

    dimension_messages = [
        issue.message for issue in bundle.fidelity_issues
        if issue.code == "low_confidence_partial_dimension"
    ]
    assert any("volume_main.depth" in message for message in dimension_messages)
    assert any("volume_main.height" in message for message in dimension_messages)
    assert not any("volume_main.width" in message for message in dimension_messages)


def test_partial_cli_mode_exports_same_buildable_subset(tmp_path: Path) -> None:
    output = tmp_path / "partial-brickhouse.json"

    bundle = write_scene_export(FIXTURE, output, front_width_studs=48, allow_partial=True)

    assert output.exists()
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_steps > 0
    assert not any(part.component == "roof" for part in bundle.brick_model.parts)


def test_partial_preview_still_refuses_an_unmeasured_primary_envelope() -> None:
    scene = load_architectural_scene(FIXTURE)
    volume = scene.volumes[0].model_copy(update={
        "width": scene.volumes[0].width.model_copy(update={"value": None})
    })
    candidate = scene.model_copy(update={"volumes": [volume, *scene.volumes[1:]]})

    with pytest.raises(ValueError, match="primary volume with resolved width, depth and height"):
        run_partial_scene_pipeline(candidate)
