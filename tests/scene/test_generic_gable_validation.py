from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.8}
USER_SOURCE = {"kind": "user_provided", "confidence": 0.99}


def _survey(*gable_facades: str) -> ArchitecturalSurvey:
    observations = []
    for index, facade in enumerate(gable_facades, start=1):
        observations.append(
            {
                "id": f"gable_{facade}_{index}",
                "kind": "roof",
                "facade": facade,
                "certainty": "certain",
                "statement": f"{facade} facade is a gable wall",
                "evidence": [{"photo_index": 1 if facade == "front" else 2, "observation": "gable outline visible"}],
                "attributes": {"facade_is_gable": True},
            }
        )
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-gable-survey",
            "name": "Generic gable survey",
            "photos": [
                {"photo_index": 1, "facade": "front", "description": "canonical front", "source": USER_SOURCE},
                {"photo_index": 2, "facade": "left", "description": "left side", "source": USER_SOURCE},
            ],
            "observations": observations,
        }
    )


def _scene(ridge_direction: str) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-gable-scene",
            "name": "Generic gable scene",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 8, "source": SOURCE},
                    "depth": {"value": 12, "source": SOURCE},
                    "height": {"value": 5, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                }
            ],
            "roofs": [
                {
                    "id": "roof",
                    "volume_id": "main",
                    "type": "gable",
                    "overhang": 0.25,
                    "ridge_direction": ridge_direction,
                    "pitch_degrees": 30,
                    "source": SOURCE,
                }
            ],
            "appearance": {"walls": {"color": "white"}, "roof": {"color": "gray"}},
        }
    )


def test_left_gable_requires_width_axis_ridge() -> None:
    assert validate_scene_against_survey(_survey("left"), _scene("width")) == []


def test_left_gable_rejects_depth_axis_ridge() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey("left"), _scene("depth"))}
    assert "gable_ridge_mismatch" in codes


def test_front_gable_requires_depth_axis_ridge_without_front_specific_rule() -> None:
    assert validate_scene_against_survey(_survey("front"), _scene("depth")) == []


def test_perpendicular_certain_gable_evidence_is_reported_as_conflicting() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey("front", "left"), _scene("depth"))}
    assert "conflicting_gable_facades" in codes
