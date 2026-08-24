import pytest
from pydantic import ValidationError

from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey, Certainty, SurveyObservation

SOURCE = {"kind": "inferred", "confidence": 0.55}
EVIDENCE = [{"photo_index": 1, "observation": "visible"}]


def test_observation_tracks_attribute_certainty_separately_from_existence() -> None:
    observation = SurveyObservation.model_validate({
        "id": "roof",
        "kind": "roof",
        "certainty": "certain",
        "statement": "roof certainly exists; exact form remains uncertain",
        "evidence": EVIDENCE,
        "attributes": {"facade_is_gable": True},
        "attribute_certainty": {"facade_is_gable": "plausible"},
    })
    assert observation.certainty is Certainty.CERTAIN
    assert observation.certainty_for_attribute("facade_is_gable") is Certainty.PLAUSIBLE


def test_attribute_certainty_cannot_reference_an_absent_attribute() -> None:
    with pytest.raises(ValidationError, match="references missing attributes"):
        SurveyObservation.model_validate({
            "id": "roof",
            "kind": "roof",
            "certainty": "certain",
            "statement": "roof visible",
            "evidence": EVIDENCE,
            "attributes": {},
            "attribute_certainty": {"facade_is_gable": "plausible"},
        })


def _survey(semantic_certainty: str) -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "attribute-certainty",
        "name": "Attribute certainty",
        "photos": [{"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE}],
        "observations": [{
            "id": "opening",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "an opening certainly exists; its semantic type is less certain",
            "evidence": EVIDENCE,
            "attributes": {"semantic_type": "door"},
            "attribute_certainty": {"semantic_type": semantic_certainty},
        }],
    })


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "attribute-certainty-scene",
        "name": "Attribute certainty",
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
        "openings": [{
            "id": "opening",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2,
            "offset_vertical": 2,
            "width": 1,
            "height": 1,
            "source": SOURCE,
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })


def test_plausible_semantic_type_does_not_become_hard_scene_constraint() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey("plausible"), _scene())}
    assert "opening_type_drift" not in codes


def test_certain_semantic_type_remains_a_hard_scene_constraint() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey("certain"), _scene())}
    assert "opening_type_drift" in codes
