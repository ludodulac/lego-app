from brickhouse.building import BuildingModel
from brickhouse.pipeline import run_m0_pipeline_model


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _model(direction: str = "rear", pitch: float = 33.0) -> BuildingModel:
    return BuildingModel.model_validate({
        "schema_version": "0.1",
        "id": f"shed-{direction}",
        "name": "Generic shed integration",
        "building_type": "house",
        "units": "m",
        "volumes": [{
            "id": "main",
            "shape": "rectangular_prism",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": 10,
            "depth": 8,
            "height": 5,
            "floors": 2,
            "source": SOURCE,
        }],
        "openings": [],
        "roofs": [{
            "id": "roof",
            "volume_id": "main",
            "type": "shed",
            "overhang": 0,
            "down_slope_direction": direction,
            "pitch_degrees": pitch,
            "source": SOURCE,
        }],
        "appearance": {},
        "metadata": {"created_from": "synthetic"},
    })


def test_rear_shed_pipeline_builds_one_slope_and_closes_high_wall() -> None:
    bundle = run_m0_pipeline_model(_model("rear"), front_width_studs=48)
    parts = bundle.brick_model.parts
    roof = [part for part in parts if part.roof_side == "slope"]
    assert roof
    assert all(part.category == "roof_tile" for part in roof)
    assert not any(part.category == "ridge_tile" for part in parts)
    assert {part.rotation_quarter_turns for part in roof} == {1}

    infill = [part for part in parts if part.placement_id.startswith("shed-wall-")]
    assert infill
    front = [part for part in infill if part.facade.value == "front"]
    rear = [part for part in infill if part.facade.value == "rear"]
    sides = [part for part in infill if part.facade.value in {"left", "right"}]
    assert front, "rear-down slope must close the elevated front wall"
    assert not rear, "the low rear eave must remain at the ordinary wall top"
    assert sides, "both side wedges must be closed below the mono-pitch plane"
    assert bundle.bom.total_parts == len(parts)
    assert bundle.assembly_plan is not None


def test_shed_rotation_encodes_all_four_down_slope_directions() -> None:
    expected = {"left": 0, "rear": 1, "right": 2, "front": 3}
    for direction, quarter_turns in expected.items():
        bundle = run_m0_pipeline_model(_model(direction), front_width_studs=48)
        roof = [part for part in bundle.brick_model.parts if part.roof_side == "slope"]
        assert roof
        assert {part.rotation_quarter_turns for part in roof} == {quarter_turns}
