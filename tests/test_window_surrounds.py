import json
from pathlib import Path

from brickhouse.building.models import BuildingModel
from brickhouse.pipeline import run_m0_pipeline_model

REFERENCE = Path("docs/examples/building-model-simple-house.json")


def test_windows_generate_facade_detail_parts_and_steps() -> None:
    building = BuildingModel.model_validate(json.loads(REFERENCE.read_text(encoding="utf-8")))
    bundle = run_m0_pipeline_model(building, front_width_studs=48)

    details = [part for part in bundle.brick_model.parts if part.component == "facade_detail"]
    assert details
    assert all(part.part_id == "BRICK_1X1" for part in details)
    assert all(part.category == "facade_detail" for part in details)

    detail_lines = [line for line in bundle.bom.lines if line.category == "facade_detail"]
    assert detail_lines
    assert sum(line.quantity for line in detail_lines) == len(details)

    detail_steps = [step for step in bundle.assembly_plan.steps if step.component == "facade_detail"]
    assert detail_steps
    assert any(step.title.startswith("Détails de façade") for step in detail_steps)
