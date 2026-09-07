from copy import deepcopy

from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey(*, ownership: str, ownership_certainty: str = "certain"):
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "ownership-scene-survey",
        "name": "Ownership scene survey",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "front view with a chimney near the target building",
            "source": SOURCE,
            "image_left_maps_to_facade_offset": "low",
        }],
        "observations": [{
            "id": "chimney-candidate",
            "kind": "chimney",
            "facade": "front",
            "certainty": "certain",
            "statement": "chimney-like architectural object visible near target roofline",
            "evidence": [{"photo_index": 1, "observation": "chimney candidate visible"}],
            "attributes": {"subject_ownership": ownership},
            "attribute_certainty": {"subject_ownership": ownership_certainty},
        }],
    })


def _scene(*, include_chimney: bool):
    chimneys = []
    if include_chimney:
        chimneys.append({
            "id": "chimney-candidate",
            "position": {"x": 2.0, "y": 2.0, "z": 5.0},
            "width": 0.5,
            "depth": 0.5,
            "height": 1.2,
            "source": SOURCE,
        })
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "ownership-scene",
        "name": "Ownership scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 8, "source": SOURCE},
            "depth": {"value": 7, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "chimneys": chimneys,
        "appearance": {"walls": {"color": "off_white"}},
    })


def _codes(survey, scene):
    return {issue.code for issue in validate_scene_against_survey(survey, scene)}


def test_certain_neighbor_chimney_cannot_be_reconstructed_as_target_scene_object():
    codes = _codes(
        _survey(ownership="external_context"),
        _scene(include_chimney=True),
    )

    assert "external_context_object_reconstructed_as_target" in codes


def test_external_context_may_remain_in_survey_without_becoming_scene_geometry():
    codes = _codes(
        _survey(ownership="external_context"),
        _scene(include_chimney=False),
    )

    assert "external_context_object_reconstructed_as_target" not in codes


def test_plausible_target_ownership_cannot_be_silently_metrified():
    codes = _codes(
        _survey(ownership="target_building", ownership_certainty="plausible"),
        _scene(include_chimney=True),
    )

    assert "uncertain_subject_ownership_metrified" in codes


def test_unresolved_ownership_cannot_be_silently_metrified():
    codes = _codes(
        _survey(ownership="unresolved", ownership_certainty="unproven"),
        _scene(include_chimney=True),
    )

    assert "uncertain_subject_ownership_metrified" in codes


def test_certain_target_owned_object_is_not_blocked_by_ownership_gate():
    codes = _codes(
        _survey(ownership="target_building"),
        _scene(include_chimney=True),
    )

    assert "external_context_object_reconstructed_as_target" not in codes
    assert "uncertain_subject_ownership_metrified" not in codes


def test_ownership_fidelity_gate_does_not_mutate_survey_or_scene():
    survey = _survey(ownership="external_context")
    scene = _scene(include_chimney=True)
    survey_before = deepcopy(survey.model_dump())
    scene_before = deepcopy(scene.model_dump())

    validate_scene_against_survey(survey, scene)

    assert survey.model_dump() == survey_before
    assert scene.model_dump() == scene_before
