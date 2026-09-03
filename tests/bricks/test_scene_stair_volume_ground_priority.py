from brickhouse.bricks.scene_architecture import _scene_bounds
from brickhouse.bricks.scene_architecture_relations import _volume_endpoint_shift
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def test_ground_endpoint_is_not_reinterpreted_as_volume_boundary_anchor():
    scene = ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "ground-priority",
            "name": "Ground connection priority",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 10, "source": SOURCE},
                    "depth": {"value": 8, "source": SOURCE},
                    "height": {"value": 6, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "run",
                    "start": {"x": -0.1, "y": 2.0, "z": 0.0},
                    "end": {"x": -0.1, "y": 3.0, "z": 1.0},
                    "width": 0.01,
                    "material": "concrete",
                    "source": SOURCE,
                }
            ],
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "dark_brown"},
            },
        }
    )
    point = scene.stairs[0].start
    origin_x, origin_y, _ = _scene_bounds(scene)

    assert scene._point_on_volume_boundary(point, scene.volumes[0])
    assert _volume_endpoint_shift(
        point,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    ) == (0, 0)
