import json
from copy import deepcopy
from pathlib import Path

from brickhouse.building.models import BuildingModel, Facade
from brickhouse.geometry import generate_building_geometry
from brickhouse.pipeline import run_m0_pipeline_model

REFERENCE = Path("docs/examples/building-model-simple-house.json")


def load_reference() -> dict:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def opening(opening_id: str, facade: str, offset: float) -> dict:
    return {
        "id": opening_id,
        "type": "window",
        "volume_id": "vol_main",
        "facade": facade,
        "offset_horizontal": offset,
        "offset_vertical": 1.0,
        "width": 1.2,
        "height": 1.3,
        "source": {"kind": "user_provided", "confidence": 1.0},
    }


def test_four_facade_openings_reach_geometry_and_brick_pipeline() -> None:
    baseline_data = load_reference()
    multi_data = deepcopy(baseline_data)
    multi_data["id"] = "building_four_facades_001"
    multi_data["name"] = "Maison quatre façades"
    multi_data["openings"].extend(
        [
            opening("window_rear_01", "rear", 2.0),
            opening("window_left_01", "left", 2.0),
            opening("window_right_01", "right", 4.0),
        ]
    )

    baseline = BuildingModel.model_validate(baseline_data)
    multi = BuildingModel.model_validate(multi_data)
    geometry = generate_building_geometry(multi)

    openings_by_facade = {
        wall.facade: len(wall.openings)
        for wall in geometry.walls
    }
    assert openings_by_facade[Facade.FRONT] == 5
    assert openings_by_facade[Facade.REAR] == 1
    assert openings_by_facade[Facade.LEFT] == 1
    assert openings_by_facade[Facade.RIGHT] == 1

    baseline_export = run_m0_pipeline_model(baseline, front_width_studs=48)
    multi_export = run_m0_pipeline_model(multi, front_width_studs=48)

    assert multi_export.brick_model.width_studs == baseline_export.brick_model.width_studs
    assert multi_export.brick_model.depth_studs == baseline_export.brick_model.depth_studs
    # Openings can increase the number of pieces because large wall bricks are
    # fragmented around a window. What matters is that the shell changes.
    assert multi_export.bom.total_parts != baseline_export.bom.total_parts
    assert multi_export.bom.lines != baseline_export.bom.lines
    assert multi_export.assembly_plan.total_parts == multi_export.bom.total_parts
