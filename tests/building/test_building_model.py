from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.building import BuildingModel, load_building_model

EXAMPLE_PATH = Path("docs/examples/building-model-simple-house.json")


def example_payload() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def assert_invalid(payload: dict) -> None:
    with pytest.raises(ValidationError):
        BuildingModel.model_validate(payload)


def test_example_loads_successfully() -> None:
    model = load_building_model(EXAMPLE_PATH)
    assert model.id == "building_simple_house_001"


def test_round_trip_preserves_model_semantically() -> None:
    model = load_building_model(EXAMPLE_PATH)
    round_tripped = BuildingModel.model_validate_json(model.model_dump_json())
    assert round_tripped == model


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_confidence_out_of_range_is_rejected(confidence: float) -> None:
    payload = example_payload()
    payload["volumes"][0]["source"]["confidence"] = confidence
    assert_invalid(payload)


@pytest.mark.parametrize("field,value", [("width", 0), ("depth", -1), ("height", 0)])
def test_non_positive_volume_dimensions_are_rejected(field: str, value: float) -> None:
    payload = example_payload()
    payload["volumes"][0][field] = value
    assert_invalid(payload)


@pytest.mark.parametrize("floors", [0, 4])
def test_invalid_floor_count_is_rejected(floors: int) -> None:
    payload = example_payload()
    payload["volumes"][0]["floors"] = floors
    assert_invalid(payload)


def test_opening_unknown_volume_is_rejected() -> None:
    payload = example_payload()
    payload["openings"][0]["volume_id"] = "missing"
    assert_invalid(payload)


def test_roof_unknown_volume_is_rejected() -> None:
    payload = example_payload()
    payload["roofs"][0]["volume_id"] = "missing"
    assert_invalid(payload)


def test_opening_past_facade_is_rejected() -> None:
    payload = example_payload()
    payload["openings"][0]["offset_horizontal"] = 9.5
    payload["openings"][0]["width"] = 1.0
    assert_invalid(payload)


def test_opening_above_volume_is_rejected() -> None:
    payload = example_payload()
    payload["openings"][0]["offset_vertical"] = 5.0
    payload["openings"][0]["height"] = 1.0
    assert_invalid(payload)


def test_overlapping_openings_are_rejected() -> None:
    payload = example_payload()
    second = copy.deepcopy(payload["openings"][0])
    second["id"] = "overlap"
    second["offset_horizontal"] = 4.8
    second["offset_vertical"] = 1.0
    payload["openings"].append(second)
    assert_invalid(payload)


def test_touching_openings_are_accepted() -> None:
    payload = example_payload()
    payload["openings"] = [
        {
            "id": "a",
            "type": "window",
            "volume_id": "vol_main",
            "facade": "front",
            "offset_horizontal": 0.0,
            "offset_vertical": 0.0,
            "width": 1.0,
            "height": 1.0,
            "source": {"kind": "user_provided", "confidence": 1.0},
        },
        {
            "id": "b",
            "type": "window",
            "volume_id": "vol_main",
            "facade": "front",
            "offset_horizontal": 1.0,
            "offset_vertical": 0.0,
            "width": 1.0,
            "height": 1.0,
            "source": {"kind": "user_provided", "confidence": 1.0},
        },
    ]
    BuildingModel.model_validate(payload)


def test_duplicate_ids_are_rejected() -> None:
    payload = example_payload()
    payload["roofs"][0]["id"] = payload["volumes"][0]["id"]
    assert_invalid(payload)


def test_two_roofs_on_same_volume_are_rejected() -> None:
    payload = example_payload()
    roof = copy.deepcopy(payload["roofs"][0])
    roof["id"] = "roof_second"
    payload["roofs"].append(roof)
    assert_invalid(payload)


def test_gable_without_ridge_direction_is_rejected() -> None:
    payload = example_payload()
    payload["roofs"][0].pop("ridge_direction")
    assert_invalid(payload)


def test_gable_without_pitch_is_rejected() -> None:
    payload = example_payload()
    payload["roofs"][0].pop("pitch_degrees")
    assert_invalid(payload)


@pytest.mark.parametrize("pitch", [0, -1, 90, 120])
def test_invalid_gable_pitch_is_rejected(pitch: float) -> None:
    payload = example_payload()
    payload["roofs"][0]["pitch_degrees"] = pitch
    assert_invalid(payload)


def test_flat_roof_with_gable_fields_is_rejected() -> None:
    payload = example_payload()
    payload["roofs"][0]["type"] = "flat"
    assert_invalid(payload)


def test_unsupported_schema_version_is_rejected() -> None:
    payload = example_payload()
    payload["schema_version"] = "0.2"
    assert_invalid(payload)


def test_units_other_than_metres_are_rejected() -> None:
    payload = example_payload()
    payload["units"] = "cm"
    assert_invalid(payload)
