from brickhouse.scene import ArchitecturalScene, project_scene_to_building


SOURCE = {"kind": "inferred", "confidence": 0.45}


def _scene():
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "terrain-unknown-amplitude",
        "name": "Terrain unknown amplitude",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "terrain": {
            "kind": "facade_grade_profiles",
            "profiles": [{
                "facade": "right",
                "start_elevation": 0.0,
                "end_elevation": None,
                "outward_extent": None,
                "source": SOURCE,
                "evidence": [{"photo_index": 2, "observation": "ground visibly rises, amplitude not safely measurable"}],
            }],
        },
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "white"},
        },
    })


def test_scene_preserves_grade_profile_when_end_elevation_is_unknown():
    scene = _scene()
    assert scene.terrain.profiles[0].end_elevation is None


def test_unknown_grade_amplitude_does_not_block_m0_projection():
    result = project_scene_to_building(_scene())
    assert result.building is not None
    assert "terrain_not_supported" in {issue.code for issue in result.issues}
    assert not result.blocked
