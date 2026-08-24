from brickhouse.bricks.export import BrickExportBundle, export_bundle_json
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _scene_with_scene_only_roof_and_recovered_terrain() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "fidelity-scene",
            "name": "Generic fidelity scene",
            "units": "m",
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
            "roofs": [
                {
                    "id": "hip-roof",
                    "volume_id": "main",
                    "type": "hip",
                    "overhang": 0.3,
                    "ridge_direction": "depth",
                    "pitch_degrees": 28,
                    "source": SOURCE,
                }
            ],
            "terrain": {
                "kind": "facade_grade_profiles",
                "profiles": [
                    {
                        "facade": "right",
                        "start_elevation": -0.6,
                        "end_elevation": 0.4,
                        "outward_extent": 1.2,
                        "source": SOURCE,
                    }
                ],
            },
            "chimneys": [
                {
                    "id": "chimney-1",
                    "position": {"x": 4, "y": 4, "z": 6},
                    "width": 0.6,
                    "depth": 0.6,
                    "height": 1.2,
                    "source": SOURCE,
                }
            ],
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "white"},
            },
        }
    )


def _scene_with_low_confidence_exterior_geometry() -> ArchitecturalScene:
    data = _scene_with_scene_only_roof_and_recovered_terrain().model_dump(mode="json")
    data["platforms"] = [
        {
            "id": "uncertain-deck",
            "host_volume_id": "main",
            "position": {"x": 10.0, "y": 2.0, "z": 1.2},
            "width": 1.5,
            "depth": 2.0,
            "thickness": 0.18,
            "material": "timber",
            "deck_board_direction": "y",
            "source": {"kind": "inferred", "confidence": 0.45},
        }
    ]
    data["stairs"] = [
        {
            "id": "uncertain-stair",
            "start": {"x": 11.0, "y": 3.0, "z": 0.0},
            "end": {"x": 11.0, "y": 2.0, "z": 1.2},
            "width": 0.8,
            "material": "concrete",
            "source": {"kind": "inferred", "confidence": 0.60},
        }
    ]
    return ArchitecturalScene.model_validate(data)


def test_scene_export_reports_only_losses_that_remain_after_scene_augmentation() -> None:
    bundle = run_m0_pipeline_scene(
        _scene_with_scene_only_roof_and_recovered_terrain(), front_width_studs=40
    )
    codes = {issue.code for issue in bundle.fidelity_issues}

    assert "roof_type_not_supported" in codes
    assert "chimney_not_supported" not in codes
    assert "terrain_not_supported" not in codes
    assert any(part.category == "terrain" for part in bundle.brick_model.parts)
    assert any(
        part.placement_id.startswith("scene-chimney:chimney-1:")
        for part in bundle.brick_model.parts
    )


def test_scene_export_surfaces_low_confidence_exterior_geometry() -> None:
    bundle = run_m0_pipeline_scene(
        _scene_with_low_confidence_exterior_geometry(), front_width_studs=40
    )
    by_object = {issue.object_id: issue for issue in bundle.fidelity_issues if issue.code == "low_confidence_exterior_geometry"}

    assert by_object["uncertain-deck"].severity == "warning"
    assert "confidence 0.45" in by_object["uncertain-deck"].message
    assert by_object["uncertain-stair"].severity == "info"
    assert "confidence 0.60" in by_object["uncertain-stair"].message
    assert any(part.placement_id.startswith("scene-platform:uncertain-deck") for part in bundle.brick_model.parts)
    assert any(part.placement_id.startswith("scene-stair:uncertain-stair") for part in bundle.brick_model.parts)


def test_fidelity_issues_survive_export_json_round_trip() -> None:
    bundle = run_m0_pipeline_scene(
        _scene_with_scene_only_roof_and_recovered_terrain(), front_width_studs=40
    )
    restored = BrickExportBundle.model_validate_json(export_bundle_json(bundle))
    assert restored.fidelity_issues == bundle.fidelity_issues
