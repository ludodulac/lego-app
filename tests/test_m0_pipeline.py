from pathlib import Path

import pytest

from brickhouse.building.models import BuildingModel
from brickhouse.bricks.export import BrickExportBundle
from brickhouse.pipeline import run_m0_pipeline, run_m0_pipeline_model, write_m0_export


REFERENCE_HOUSE = Path("docs/examples/building-model-simple-house.json")


def _brick_span(part_id: str) -> int:
    return int(part_id.rsplit("X", 1)[-1])


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


def test_reference_house_closes_both_gable_ends():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    gables = [part for part in bundle.brick_model.parts if part.placement_id.startswith("gable-")]
    assert gables
    assert {part.facade.value for part in gables} == {"front", "rear"}
    assert all(part.component == "wall" and part.category == "brick" for part in gables)
    assert any(part.part_id != "BRICK_1X1" for part in gables)
    assert {part.y_studs for part in gables if part.facade.value == "front"} == {0}
    assert {part.y_studs for part in gables if part.facade.value == "rear"} == {bundle.brick_model.depth_studs - 1}
    front_levels = sorted({part.z_plates for part in gables if part.facade.value == "front"})
    rear_levels = sorted({part.z_plates for part in gables if part.facade.value == "rear"})
    assert front_levels == rear_levels
    assert len(front_levels) > 1
    widths_by_level = [sum(_brick_span(part.part_id) for part in gables if part.facade.value == "front" and part.z_plates == level) for level in front_levels]
    assert widths_by_level == sorted(widths_by_level, reverse=True)
    assert widths_by_level[-1] < widths_by_level[0]


def test_reference_pipeline_is_deterministic():
    first = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    second = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    assert first.model_dump_json(exclude_none=True) == second.model_dump_json(exclude_none=True)


def test_multi_volume_build_uses_one_shared_grid_and_keeps_secondary_walls():
    building = BuildingModel.model_validate({
        "schema_version": "0.1",
        "id": "multi-house",
        "name": "Multi volume house",
        "building_type": "house",
        "units": "m",
        "volumes": [
            {"id": "main", "shape": "rectangular_prism", "position": {"x": 0, "y": 0, "z": 0}, "width": 10, "depth": 8, "height": 7.5, "floors": 3, "source": {"kind": "user_provided", "confidence": 0.99}},
            {"id": "annex", "shape": "rectangular_prism", "position": {"x": -2, "y": 5, "z": 0}, "width": 2, "depth": 3, "height": 2.5, "floors": 1, "source": {"kind": "inferred", "confidence": 0.6}},
        ],
        "openings": [
            {"id": "annex_door", "type": "door", "volume_id": "annex", "facade": "left", "offset_horizontal": 0.5, "offset_vertical": 0, "width": 1.0, "height": 2.0, "source": {"kind": "inferred", "confidence": 0.5}}
        ],
        "roofs": [
            {"id": "main_roof", "volume_id": "main", "type": "gable", "overhang": 0.25, "ridge_direction": "depth", "pitch_degrees": 20, "source": {"kind": "inferred", "confidence": 0.6}},
            {"id": "annex_roof", "volume_id": "annex", "type": "flat", "overhang": 0.05, "source": {"kind": "inferred", "confidence": 0.5}},
        ],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
        "metadata": {"created_from": "photo_analysis"},
    })
    bundle = run_m0_pipeline_model(building, front_width_studs=48)
    assert bundle.volume_id == "composite"
    assert bundle.brick_model.width_studs > 48
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert any(part.placement_id.startswith("main:") for part in bundle.brick_model.parts)
    assert any(part.placement_id.startswith("annex:") for part in bundle.brick_model.parts)
    assert any(part.placement_id.startswith("main:roof-") for part in bundle.brick_model.parts)
    assert not any(part.placement_id.startswith("annex:roof-") for part in bundle.brick_model.parts)


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
