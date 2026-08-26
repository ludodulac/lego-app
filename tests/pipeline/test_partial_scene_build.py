from pathlib import Path

import pytest

from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene_cli import load_architectural_scene, write_scene_export


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_current_brickhouse_scene_can_build_trustworthy_core_before_roof_is_resolved() -> None:
    scene = load_architectural_scene(FIXTURE)

    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)

    assert bundle.brick_model.parts
    assert any(part.component == "wall" for part in bundle.brick_model.parts)
    assert not any(part.component == "roof" for part in bundle.brick_model.parts)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan.steps[0].phase == "Structure"
    codes = {issue.code for issue in bundle.fidelity_issues}
    assert "partial_preview_roof_omitted" in codes


def test_partial_cli_mode_exports_same_buildable_subset(tmp_path: Path) -> None:
    output = tmp_path / "partial-brickhouse.json"

    bundle = write_scene_export(FIXTURE, output, front_width_studs=48, allow_partial=True)

    assert output.exists()
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_steps > 0
    assert not any(part.component == "roof" for part in bundle.brick_model.parts)


def test_partial_preview_still_refuses_an_unmeasured_envelope() -> None:
    scene = load_architectural_scene(FIXTURE)
    volume = scene.volumes[0].model_copy(update={
        "width": scene.volumes[0].width.model_copy(update={"value": None})
    })
    candidate = scene.model_copy(update={"volumes": [volume, *scene.volumes[1:]]})

    with pytest.raises(ValueError, match="resolved width, depth and height"):
        run_partial_scene_pipeline(candidate)
