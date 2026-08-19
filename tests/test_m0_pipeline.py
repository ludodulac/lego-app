from pathlib import Path

import pytest

from brickhouse.bricks.export import BrickExportBundle
from brickhouse.pipeline import run_m0_pipeline, write_m0_export


REFERENCE_HOUSE = Path("docs/examples/building-model-simple-house.json")


def test_reference_house_runs_end_to_end():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)

    assert bundle.building_id == "building_simple_house_001"
    assert bundle.brick_model.width_studs == 48
    assert bundle.brick_model.depth_studs == 38
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.bom.total_parts > 0
    assert bundle.bom.unique_part_types > 1
    assert any(part.component == "wall" for part in bundle.brick_model.parts)
    assert any(part.component == "roof" for part in bundle.brick_model.parts)


def test_reference_pipeline_is_deterministic():
    first = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    second = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)

    assert first.model_dump_json(exclude_none=True) == second.model_dump_json(exclude_none=True)


def test_write_export_round_trips(tmp_path: Path):
    output = tmp_path / "house-export.json"
    bundle = write_m0_export(REFERENCE_HOUSE, output, front_width_studs=48)

    assert output.exists()
    restored = BrickExportBundle.model_validate_json(output.read_text(encoding="utf-8"))
    assert restored == bundle


def test_invalid_front_width_is_rejected():
    with pytest.raises(ValueError, match="front_width_studs"):
        run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=0)


def test_missing_input_propagates_file_error(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        run_m0_pipeline(tmp_path / "missing.json")
