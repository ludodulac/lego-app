import math

from brickhouse.building.models import BuildingModel
from brickhouse.geometry import generate_building_geometry


def make_model(**changes):
    data = {
        "schema_version": "0.1",
        "id": "b1",
        "name": "Test",
        "building_type": "detached_house",
        "units": "m",
        "volumes": [
            {
                "id": "v1",
                "shape": "rectangular_prism",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": 10,
                "depth": 8,
                "height": 6,
                "floors": 2,
                "source": {"kind": "user_provided", "confidence": 1},
            }
        ],
        "openings": [],
        "roofs": [],
        "appearance": {},
        "metadata": {"created_from": "synthetic"},
    }
    data.update(changes)
    return BuildingModel.model_validate(data)


def xyz(point):
    return (point.x, point.y, point.z)


def test_four_walls_are_generated():
    geometry = generate_building_geometry(make_model())
    assert len(geometry.walls) == 4
    front = next(wall for wall in geometry.walls if wall.facade.value == "front")
    assert [xyz(corner) for corner in front.corners] == [
        (0, 0, 0),
        (10, 0, 0),
        (10, 0, 6),
        (0, 0, 6),
    ]


def test_rear_wall_orientation_is_exterior_left_to_right():
    geometry = generate_building_geometry(make_model())
    rear = next(wall for wall in geometry.walls if wall.facade.value == "rear")
    assert [xyz(corner) for corner in rear.corners] == [
        (10, 8, 0),
        (0, 8, 0),
        (0, 8, 6),
        (10, 8, 6),
    ]


def test_front_opening_world_coordinates():
    model = make_model(
        openings=[
            {
                "id": "o1",
                "type": "window",
                "volume_id": "v1",
                "facade": "front",
                "offset_horizontal": 2,
                "offset_vertical": 1,
                "width": 1.5,
                "height": 2,
                "source": {"kind": "observed", "confidence": 0.9},
            }
        ]
    )
    geometry = generate_building_geometry(model)
    front = next(wall for wall in geometry.walls if wall.facade.value == "front")
    assert [xyz(corner) for corner in front.openings[0].corners] == [
        (2, 0, 1),
        (3.5, 0, 1),
        (3.5, 0, 3),
        (2, 0, 3),
    ]


def test_rear_offset_is_measured_from_exterior_left():
    model = make_model(
        openings=[
            {
                "id": "o1",
                "type": "window",
                "volume_id": "v1",
                "facade": "rear",
                "offset_horizontal": 2,
                "offset_vertical": 1,
                "width": 1,
                "height": 1,
                "source": {"kind": "observed", "confidence": 0.9},
            }
        ]
    )
    geometry = generate_building_geometry(model)
    rear = next(wall for wall in geometry.walls if wall.facade.value == "rear")
    assert [xyz(corner) for corner in rear.openings[0].corners] == [
        (8, 8, 1),
        (7, 8, 1),
        (7, 8, 2),
        (8, 8, 2),
    ]


def test_flat_roof_with_overhang():
    model = make_model(
        roofs=[
            {
                "id": "r1",
                "volume_id": "v1",
                "type": "flat",
                "overhang": 0.5,
                "source": {"kind": "observed", "confidence": 1},
            }
        ]
    )
    geometry = generate_building_geometry(model)
    assert len(geometry.roof_planes) == 1
    assert [xyz(corner) for corner in geometry.roof_planes[0].corners] == [
        (-0.5, -0.5, 6),
        (10.5, -0.5, 6),
        (10.5, 8.5, 6),
        (-0.5, 8.5, 6),
    ]


def test_gable_depth_ridge_height():
    model = make_model(
        roofs=[
            {
                "id": "r1",
                "volume_id": "v1",
                "type": "gable",
                "ridge_direction": "depth",
                "pitch_degrees": 45,
                "overhang": 0,
                "source": {"kind": "observed", "confidence": 1},
            }
        ]
    )
    geometry = generate_building_geometry(model)
    assert len(geometry.roof_planes) == 2
    assert math.isclose(geometry.roof_planes[0].corners[1].z, 11, abs_tol=1e-9)
    assert geometry.roof_planes[0].corners[1].x == 5


def test_gable_width_ridge_height():
    model = make_model(
        roofs=[
            {
                "id": "r1",
                "volume_id": "v1",
                "type": "gable",
                "ridge_direction": "width",
                "pitch_degrees": 45,
                "overhang": 0,
                "source": {"kind": "observed", "confidence": 1},
            }
        ]
    )
    geometry = generate_building_geometry(model)
    assert len(geometry.roof_planes) == 2
    assert math.isclose(geometry.roof_planes[0].corners[2].z, 10, abs_tol=1e-9)
    assert geometry.roof_planes[0].corners[2].y == 4


def test_multiple_volumes_generate_four_walls_each():
    volumes = [
        {
            "id": "v1",
            "shape": "rectangular_prism",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": 10,
            "depth": 8,
            "height": 6,
            "floors": 2,
            "source": {"kind": "user_provided", "confidence": 1},
        },
        {
            "id": "v2",
            "shape": "rectangular_prism",
            "position": {"x": 10, "y": 0, "z": 0},
            "width": 3,
            "depth": 4,
            "height": 3,
            "floors": 1,
            "source": {"kind": "user_provided", "confidence": 1},
        },
    ]
    assert len(generate_building_geometry(make_model(volumes=volumes)).walls) == 8


def test_geometry_serialization_is_deterministic():
    model = make_model(
        roofs=[
            {
                "id": "r1",
                "volume_id": "v1",
                "type": "gable",
                "ridge_direction": "depth",
                "pitch_degrees": 35,
                "overhang": 0.3,
                "source": {"kind": "observed", "confidence": 1},
            }
        ]
    )
    first = generate_building_geometry(model).model_dump_json()
    second = generate_building_geometry(model).model_dump_json()
    assert first == second
