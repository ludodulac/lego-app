from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.projection import project_scene_to_building


SOURCE = {"kind": "inferred", "confidence": 0.45}


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-exact-gable",
        "name": "Generic exact gable",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "roofs": [{
            "id": "roof",
            "volume_id": "main",
            "type": "gable",
            "overhang": 0.2,
            "ridge_direction": "depth",
            "pitch_degrees": 17.0,
            "source": SOURCE,
            "evidence": [{"photo_index": 1, "observation": "generic exact gable regression"}],
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}},
    })


def test_exact_gable_survives_scene_projection_without_requantization() -> None:
    scene = _scene()
    projection = project_scene_to_building(scene)

    assert projection.building is not None
    assert "gable_geometry_incomplete" not in {issue.code for issue in projection.issues}

    roof = projection.building.roofs[0]
    assert roof.type.value == "gable"
    assert roof.ridge_direction.value == "depth"
    assert roof.pitch_degrees == 17.0
