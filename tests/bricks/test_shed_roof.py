from brickhouse.building import BuildingModel
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.shed_roof import generate_spatial_shed_roof, validate_shed_roof_support
from brickhouse.geometry import generate_building_geometry


def _model(direction: str = "rear", pitch: float = 33) -> BuildingModel:
    return BuildingModel.model_validate({
        "schema_version": "0.1",
        "id": "generic-shed",
        "name": "Generic shed",
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
            "source": {"kind": "inferred", "confidence": 0.7},
        }],
        "openings": [],
        "roofs": [{
            "id": "roof",
            "volume_id": "main",
            "type": "shed",
            "overhang": 0,
            "down_slope_direction": direction,
            "pitch_degrees": pitch,
            "source": {"kind": "inferred", "confidence": 0.7},
        }],
        "appearance": {},
        "metadata": {"created_from": "synthetic"},
    })


def _roof(direction="rear"):
    geometry = generate_building_geometry(_model(direction))
    shell = generate_building_brick_shell(geometry, 48)
    return generate_spatial_shed_roof(geometry, shell), shell


def test_shed_roof_is_one_connected_slope_without_ridge() -> None:
    roof, shell = _roof("rear")
    assert roof.down_slope_direction.value == "rear"
    assert {placement.side for placement in roof.placements} == {"slope"}
    validate_shed_roof_support(roof, shell)


def test_rear_down_slope_is_low_at_rear_and_high_at_front() -> None:
    roof, _ = _roof("rear")
    by_y = {}
    for placement in roof.placements:
        by_y.setdefault(placement.y_studs, placement.z_plates)
    assert by_y[max(by_y)] == min(by_y.values())
    assert by_y[min(by_y)] == max(by_y.values())


def test_right_down_slope_uses_x_axis() -> None:
    roof, _ = _roof("right")
    by_x = {}
    for placement in roof.placements:
        by_x.setdefault(placement.x_studs, placement.z_plates)
    assert by_x[max(by_x)] == min(by_x.values())
    assert by_x[min(by_x)] == max(by_x.values())
