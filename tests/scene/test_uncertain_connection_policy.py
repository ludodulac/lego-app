from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
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


def _disconnected_scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "uncertain-connection-scene",
        "name": "Conservative disconnected geometry",
        "units": "m",
        "volumes": [{
            "id": "main", "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE}, "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE}, "floors": 2, "source": SOURCE,
        }],
        "platforms": [{
            "id": "deck", "host_volume_id": "main", "position": {"x": -1.5, "y": 4.5, "z": 2.2},
            "width": 1.5, "depth": 2.0, "thickness": 0.2, "material": "timber", "source": SOURCE,
        }],
        "stairs": [{
            "id": "stair", "start": {"x": -1.0, "y": 1.0, "z": 0.0},
            "end": {"x": -1.0, "y": 2.5, "z": 1.0}, "width": 0.9, "material": "concrete", "source": SOURCE,
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
    })


def test_plausible_hidden_connection_does_not_force_fake_metric_link() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey("plausible"), _disconnected_scene())}
    assert "certain_connection_broken" not in codes
    assert "certain_connection_blocked_by_platform_edge" not in codes


def test_same_geometry_is_rejected_when_connection_is_certain() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey("certain"), _disconnected_scene())}
    assert "certain_connection_broken" in codes
