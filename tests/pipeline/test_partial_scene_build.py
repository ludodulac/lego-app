from pathlib import Path

import pytest

from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene_cli import load_architectural_scene, write_scene_export


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_current_brickhouse_scene_can_build_useful_core_before_roof_is_resolved() -> None:
    scene = load_architectural_scene(FIXTURE)

    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)

    assert bundle.brick_model.parts
    assert bundle.brick_model.volume_id == "composite"
    assert any(part.component == "wall" for part in bundle.brick_model.parts)
    assert any(part.placement_id.startswith("lower_exterior_volume:") for part in bundle.brick_model.parts)
    assert not any(part.component == "roof" for part in bundle.brick_model.parts)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan.steps[0].phase == "Structure"
    codes = {issue.code for issue in bundle.fidelity_issues}
    assert "partial_preview_roof_omitted" in codes
    assert "partial_preview_secondary_volume_omitted" not in codes
    assert "low_confidence_partial_dimension" in codes
    assert "low_confidence_partial_opening_geometry" in codes


def test_partial_preview_recovers_support_safe_platform_and_stair() -> None:
    scene = load_architectural_scene(FIXTURE)

    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)
    placement_ids = {part.placement_id for part in bundle.brick_model.parts}

    assert any(item.startswith("scene-platform:timber_deck:") for item in placement_ids)
    assert any(item.startswith("scene-stair:exterior_stair:") for item in placement_ids)
    omitted_ids = {
        issue.object_id
        for issue in bundle.fidelity_issues
        if issue.code == "partial_preview_exterior_object_omitted"
    }
    assert "timber_deck" not in omitted_ids
    assert "exterior_stair" not in omitted_ids


def test_partial_preview_omits_stair_with_unresolved_endpoint_support_without_hiding_platform() -> None:
    scene = load_architectural_scene(FIXTURE)
    stair = scene.stairs[0]
    unsupported_end = stair.end.model_copy(update={"x": 3.0, "y": 6.0, "z": 2.5})
    unsupported_stair = stair.model_copy(update={"end": unsupported_end})
    candidate = scene.model_copy(update={"stairs": [unsupported_stair]})

    bundle = run_partial_scene_pipeline(candidate, front_width_studs=48)
    placement_ids = {part.placement_id for part in bundle.brick_model.parts}

    assert any(item.startswith("scene-platform:timber_deck:") for item in placement_ids)
    assert not any(item.startswith("scene-stair:exterior_stair:") for item in placement_ids)
    omission = next(
        issue for issue in bundle.fidelity_issues
        if issue.code == "partial_preview_exterior_object_omitted"
        and issue.object_id == "exterior_stair"
    )
    assert "No support or hidden connection is invented" in omission.message


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
