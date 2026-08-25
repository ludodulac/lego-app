from brickhouse.building import BuildingModel
from brickhouse.geometry import generate_building_geometry


def _model(direction: str) -> BuildingModel:
    return BuildingModel.model_validate({
        "schema_version": "0.1",
        "id": "shed-geometry",
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
            "pitch_degrees": 30,
            "source": {"kind": "inferred", "confidence": 0.7},
        }],
        "appearance": {},
        "metadata": {"created_from": "synthetic"},
    })


def _edge_z(plane, *, y=None, x=None):
    points = plane.corners
    if y is not None:
        points = [point for point in points if point.y == y]
    if x is not None:
        points = [point for point in points if point.x == x]
    return {round(point.z, 6) for point in points}


def test_rear_down_slope_has_high_front_and_low_rear() -> None:
    plane = generate_building_geometry(_model("rear")).roof_planes[0]
    assert plane.side == "slope"
    assert plane.down_slope_direction.value == "rear"
    assert _edge_z(plane, y=8) == {5.0}
    assert min(_edge_z(plane, y=0)) > 5.0


def test_front_down_slope_reverses_high_and_low_edges() -> None:
    plane = generate_building_geometry(_model("front")).roof_planes[0]
    assert _edge_z(plane, y=0) == {5.0}
    assert min(_edge_z(plane, y=8)) > 5.0


def test_right_down_slope_uses_width_axis_not_depth_axis() -> None:
    plane = generate_building_geometry(_model("right")).roof_planes[0]
    assert _edge_z(plane, x=10) == {5.0}
    assert min(_edge_z(plane, x=0)) > 5.0
