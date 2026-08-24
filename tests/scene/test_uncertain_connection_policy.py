from brickhouse.scene import ArchitecturalScene, SceneSurveySeverity, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.55}


def _survey(certainty: str) -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "uncertain-connection-survey",
        "name": "Uncertain exterior connection",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "canonical front", "source": SOURCE},
            {"photo_index": 2, "facade": "left", "description": "partly occluded exterior circulation", "source": SOURCE},
        ],
        "observations": [
            {"id": "stair", "kind": "stair", "facade": "left", "certainty": "certain", "statement": "lower stair is visible", "evidence": [{"photo_index": 2, "observation": "stair visible until it disappears behind wall"}]},
            {"id": "deck", "kind": "platform", "facade": "left", "certainty": "certain", "statement": "raised deck is visible", "evidence": [{"photo_index": 2, "observation": "deck visible beyond occlusion"}]},
        ],
        "relations": [
            {"id": "hidden-link", "kind": "connects_to", "subject_id": "stair", "object_id": "deck", "certainty": certainty, "statement": "their hidden connection is not directly visible", "evidence": [{"photo_index": 2, "observation": "both disappear into the same occluded zone"}]}
        ],
    })


def _scene_without_hidden_geometry() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "uncertain-connection-scene",
        "name": "Conservative omitted geometry",
        "units": "m",
        "volumes": [{
            "id": "main", "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE}, "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE}, "floors": 2, "source": SOURCE,
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
        "notes": "stair omitted and deck omitted: visible architectural existence remains in Survey, but hidden metric continuation is not evidenced.",
    })


def test_plausible_hidden_connection_does_not_force_fake_metric_link() -> None:
    issues = validate_scene_against_survey(_survey("plausible"), _scene_without_hidden_geometry())
    codes = {issue.code for issue in issues}
    assert "certain_connection_broken" not in codes
    assert "certain_stair_not_geometrically_encoded" in codes
    assert "certain_platform_not_geometrically_encoded" in codes


def test_even_certain_topological_connection_does_not_justify_hidden_metric_geometry() -> None:
    issues = validate_scene_against_survey(_survey("certain"), _scene_without_hidden_geometry())
    codes = {issue.code for issue in issues}
    assert "certain_connection_broken" not in codes
    omitted = [
        issue for issue in issues
        if issue.code in {"certain_stair_not_geometrically_encoded", "certain_platform_not_geometrically_encoded"}
    ]
    assert len(omitted) == 2
    assert all(issue.severity is SceneSurveySeverity.WARNING for issue in omitted)
