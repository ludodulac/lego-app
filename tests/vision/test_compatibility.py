import json
from pathlib import Path

from brickhouse.building.models import BuildingModel
from brickhouse.vision.compatibility import assess_m0_compatibility

REFERENCE = Path("docs/examples/building-model-simple-house.json")


def _building() -> BuildingModel:
    return BuildingModel.model_validate(json.loads(REFERENCE.read_text(encoding="utf-8")))


def test_reference_gable_house_is_buildable():
    result = assess_m0_compatibility(_building())
    assert result.buildable is True
    assert result.blockers == []


def test_flat_roof_is_explicitly_reported_without_blocking_walls():
    building = _building()
    building.roofs[0].type = "flat"
    building.roofs[0].ridge_direction = None
    building.roofs[0].pitch_degrees = None
    result = assess_m0_compatibility(building)
    assert result.buildable is True
    assert any("toiture plate" in warning for warning in result.warnings)


def test_multiple_volumes_are_buildable_on_shared_grid():
    building = _building()
    second = building.volumes[0].model_copy(update={"id": "secondary", "position": {"x": 12, "y": 0, "z": 0}})
    building.volumes.append(second)
    result = assess_m0_compatibility(building)
    assert result.buildable is True
    assert any("volumes rectangulaires multiples" in warning for warning in result.warnings)
