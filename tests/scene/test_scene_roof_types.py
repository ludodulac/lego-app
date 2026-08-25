from brickhouse.scene import ArchitecturalScene, SceneRoofType, project_scene_to_building


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _scene(roof_payload):
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "roof-types",
            "name": "Roof type preservation",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 10, "source": SOURCE},
                    "depth": {"value": 8, "source": SOURCE},
                    "height": {"value": 5, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                }
            ],
            "roofs": [{"id": "roof", "volume_id": "main", "overhang": 0.25, "source": SOURCE, **roof_payload}],
            "appearance": {"walls": {"color": "white"}, "roof": {"color": "gray"}},
        }
    )


def test_scene_accepts_hip_roof_without_forcing_gable_geometry() -> None:
    scene = _scene({"type": "hip", "pitch_degrees": 28})
    assert scene.roofs[0].type is SceneRoofType.HIP
    assert scene.roofs[0].ridge_direction is None


def test_scene_accepts_shed_roof_without_fake_ridge() -> None:
    scene = _scene({"type": "shed", "pitch_degrees": 12})
    assert scene.roofs[0].type is SceneRoofType.SHED
    assert scene.roofs[0].ridge_direction is None


def test_projection_blocks_unsupported_roof_instead_of_producing_open_building() -> None:
    scene = _scene({"type": "shed", "pitch_degrees": 12})
    result = project_scene_to_building(scene)
    assert result.building is None
    assert result.blocked
    issues = [issue for issue in result.issues if issue.code == "roof_type_not_supported"]
    assert len(issues) == 1
    assert issues[0].object_id == "roof"
    assert issues[0].severity.value == "blocker"
    assert "open building" in issues[0].message


def test_supported_gable_still_projects_normally() -> None:
    scene = _scene({"type": "gable", "ridge_direction": "depth", "pitch_degrees": 30})
    result = project_scene_to_building(scene)
    assert result.building is not None
    assert len(result.building.roofs) == 1
    assert result.building.roofs[0].type.value == "gable"
    assert not any(issue.code == "roof_type_not_supported" for issue in result.issues)
