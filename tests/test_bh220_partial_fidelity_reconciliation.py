from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _support_safe_exterior_scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-support-safe-exterior",
            "name": "Generic support-safe exterior",
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
            "openings": [],
            "roofs": [
                {
                    "id": "roof-main",
                    "volume_id": "main",
                    "type": "flat",
                    "overhang": 0.2,
                    "source": SOURCE,
                }
            ],
            "platforms": [
                {
                    "id": "side-deck",
                    "host_volume_id": "main",
                    "position": {"x": 10, "y": 2, "z": 1},
                    "width": 2,
                    "depth": 2,
                    "thickness": 0.2,
                    "material": "timber",
                    "deck_board_direction": "x",
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "deck-stair",
                    "start": {"x": 11, "y": 3, "z": 0},
                    "end": {"x": 11, "y": 3, "z": 1},
                    "width": 1,
                    "material": "timber",
                    "source": SOURCE,
                }
            ],
            "chimneys": [
                {
                    "id": "roof-chimney",
                    "position": {"x": 4, "y": 4, "z": 6},
                    "width": 0.6,
                    "depth": 0.6,
                    "height": 1.2,
                    "source": SOURCE,
                }
            ],
            "appearance": {},
        }
    )


def test_partial_preview_does_not_report_recovered_exterior_objects_as_unsupported() -> None:
    bundle = run_partial_scene_pipeline(_support_safe_exterior_scene(), front_width_studs=40)
    issues = {(issue.code, issue.object_id) for issue in bundle.fidelity_issues}

    assert ("platform_not_supported", "side-deck") not in issues
    assert ("stair_not_supported", "deck-stair") not in issues
    assert ("chimney_not_supported", "roof-chimney") not in issues
    assert not any(
        issue.code == "partial_preview_exterior_object_omitted"
        and issue.object_id in {"side-deck", "deck-stair", "roof-chimney"}
        for issue in bundle.fidelity_issues
    )

    placement_ids = {part.placement_id for part in bundle.brick_model.parts}
    assert any(item.startswith("scene-platform:side-deck") for item in placement_ids)
    assert any(item.startswith("scene-stair:deck-stair") for item in placement_ids)
    assert any(item.startswith("scene-chimney:roof-chimney:") for item in placement_ids)
