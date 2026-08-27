from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene import ArchitecturalScene


def _scene(*, reveal_value=None, reveal_confidence=0.4):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "recess-fidelity",
        "name": "Recess fidelity",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10.0, "source": {"kind": "user_provided", "confidence": 1.0}, "evidence": []},
            "depth": {"value": 8.0, "source": {"kind": "user_provided", "confidence": 1.0}, "evidence": []},
            "height": {"value": 6.0, "source": {"kind": "user_provided", "confidence": 1.0}, "evidence": []},
            "floors": 2,
            "source": {"kind": "user_provided", "confidence": 1.0},
            "evidence": [],
        }],
        "openings": [],
        "roofs": [],
        "terrain": None,
        "chimneys": [],
        "platforms": [],
        "stairs": [],
        "equipment": [],
        "visibility": [],
        "relations": [],
        "platform_structure_observations": [],
        "wall_profile_observations": [{
            "id": "front-recess",
            "volume_id": "main",
            "facade": "front",
            "openings_recessed": True,
            "wall_thickness": None,
            "reveal_depth": {
                "value": reveal_value,
                "source": {"kind": "inferred", "confidence": reveal_confidence},
                "evidence": [{"photo_index": 1, "observation": "Side view shows the opening set behind the facade plane."}],
            },
            "source": {"kind": "observed", "confidence": 0.9},
            "evidence": [{"photo_index": 1, "observation": "Opening is visibly recessed."}],
        }],
        "appearance": {},
    })


def test_partial_preview_reports_observed_recess_when_depth_is_unknown():
    bundle = run_partial_scene_pipeline(_scene())
    issue = next(item for item in bundle.fidelity_issues if item.code == "observed_recess_depth_unresolved")
    assert issue.object_id == "front-recess"
    assert "visibly recessed" in issue.message
    assert "inventing a depth" in issue.message


def test_partial_preview_does_not_report_recess_as_unresolved_when_depth_is_reliable():
    bundle = run_partial_scene_pipeline(_scene(reveal_value=0.25, reveal_confidence=0.8))
    assert all(item.code != "observed_recess_depth_unresolved" for item in bundle.fidelity_issues)
