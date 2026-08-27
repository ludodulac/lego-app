from brickhouse.scene import ArchitecturalScene, project_scene_to_building, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "observed", "confidence": 0.95}
VISUAL = {
    "shutter_count": 2,
    "shutter_style": "folding",
    "shutter_color": "white",
    "shutter_state": "folded_open",
}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "shutter-survey",
        "name": "Shutter survey",
        "photos": [{
            "photo_index": 1,
            "facade": "right",
            "description": "Right facade with visible shutters",
            "source": SOURCE,
            "image_left_maps_to_facade_offset": "low",
        }, {
            "photo_index": 2,
            "facade": "front",
            "description": "Canonical front",
            "source": SOURCE,
            "image_left_maps_to_facade_offset": "low",
        }],
        "observations": [{
            "id": "right_window_upper",
            "kind": "opening",
            "facade": "right",
            "certainty": "certain",
            "statement": "Upper right window with white folding shutters visibly folded open",
            "evidence": [{"photo_index": 1, "observation": "Two white folding shutters are visibly folded open beside the window."}],
            "attributes": {"semantic_type": "window"},
            "opening_visual": VISUAL,
        }],
    })


def _scene(*, shutter_state="folded_open") -> ArchitecturalScene:
    visual = dict(VISUAL)
    if shutter_state is None:
        visual.pop("shutter_state")
    else:
        visual["shutter_state"] = shutter_state
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "shutter-scene",
        "name": "Shutter scene",
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
            "id": "right_window_upper",
            "type": "window",
            "volume_id": "main",
            "facade": "right",
            "offset_horizontal": 3,
            "offset_vertical": 3,
            "width": 1.2,
            "height": 1.5,
            "source": SOURCE,
            "opening_visual": visual,
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })


def test_shutter_state_survives_scene_to_building_projection() -> None:
    result = project_scene_to_building(_scene())
    assert not result.blocked
    visual = result.building.openings[0].opening_visual
    assert visual is not None
    assert visual.shutter_count == 2
    assert visual.shutter_style == "folding"
    assert visual.shutter_color == "white"
    assert visual.shutter_state == "folded_open"


def test_observed_shutter_state_cannot_disappear_from_scene() -> None:
    issues = validate_scene_against_survey(_survey(), _scene(shutter_state=None))
    assert any(
        issue.code == "opening_visual_detail_lost"
        and issue.object_id == "right_window_upper"
        and "shutter_state" in issue.message
        for issue in issues
    )


def test_exact_shutter_state_preservation_passes_fidelity_guard() -> None:
    issues = validate_scene_against_survey(_survey(), _scene())
    assert not any(
        issue.code == "opening_visual_detail_lost" and issue.object_id == "right_window_upper"
        for issue in issues
    )
