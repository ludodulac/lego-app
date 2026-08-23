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


def test_scene_export_reports_only_losses_that_remain_after_scene_augmentation() -> None:
    bundle = run_m0_pipeline_scene(
        _scene_with_scene_only_roof_and_recovered_terrain(), front_width_studs=40
    )
    codes = {issue.code for issue in bundle.fidelity_issues}

    assert "roof_type_not_supported" in codes
    assert "chimney_not_supported" in codes
    # Terrain is absent from BuildingModel 0.1 but is restored by the Scene-aware
    # LEGO augmentation, so it must not be advertised as a final export loss.
    assert "terrain_not_supported" not in codes
    assert any(part.category == "terrain" for part in bundle.brick_model.parts)


def test_fidelity_issues_survive_export_json_round_trip() -> None:
    bundle = run_m0_pipeline_scene(
        _scene_with_scene_only_roof_and_recovered_terrain(), front_width_studs=40
    )
    restored = BrickExportBundle.model_validate_json(export_bundle_json(bundle))
    assert restored.fidelity_issues == bundle.fidelity_issues
