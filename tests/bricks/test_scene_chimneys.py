from pathlib import Path

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


FIXTURE = Path("tests/fixtures/architectural_scene_real_house_v02.json")


def test_scene_pipeline_renders_metric_chimney_into_brick_model_bom_and_assembly() -> None:
    scene = ArchitecturalScene.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)

    chimney_parts = [
        part
        for part in bundle.brick_model.parts
        if part.placement_id.startswith("scene-chimney:chimney_main_01:")
    ]
    assert chimney_parts
    assert all(part.part_id == "BRICK_1X1" for part in chimney_parts)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_steps > 0
    assert "chimney_not_supported" not in {issue.code for issue in bundle.fidelity_issues}
