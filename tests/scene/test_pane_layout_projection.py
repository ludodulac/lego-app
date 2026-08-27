from brickhouse.scene import ArchitecturalScene, project_scene_to_building, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "observed", "confidence": 0.95}
LAYOUT = "two_over_two_upper_rectangular_lower_squarer"
VISUAL = {
    "leaf_count": 2,
    "pane_count": 4,
    "pane_layout": LAYOUT,
    "glazing": "clear_to_dark_reflective",
}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "door-pane-survey",
        "name": "Door pane survey",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "Front glazed access",
            "source": SOURCE,
            "image_left_maps_to_facade_offset": "low",
        }],
        "observations": [{
            "id": "front_glazed_door_lower_right",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "Two-leaf glazed access with four visible panes",
            "evidence": [{
                "photo_index": 1,
                "observation": "Two upper rectangular panes and two lower squarer panes are visible.",
            }],
            "attributes": {"semantic_type": "door", "physical_object_count": 1},
            "opening_visual": VISUAL,
        }],
    })


def _scene(*, pane_layout=LAYOUT) -> ArchitecturalScene:
    visual = dict(VISUAL)
    if pane_layout is None:
        visual.pop("pane_layout")
    else:
        visual["pane_layout"] = pane_layout
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "door-pane-scene",
        "name": "Door pane scene",
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
            "id": "front_glazed_door_lower_right",
            "type": "door",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 5.85,
            "offset_vertical": 0,
            "width": 1.9,
            "height": 2.25,
            "source": SOURCE,
            "opening_visual": visual,
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })


def test_pane_layout_survives_scene_to_building_projection() -> None:
    result = project_scene_to_building(_scene())
    assert not result.blocked
    visual = result.building.openings[0].opening_visual
    assert visual is not None
    assert visual.leaf_count == 2
    assert visual.pane_count == 4
    assert visual.pane_layout == LAYOUT


def test_observed_pane_layout_cannot_silently_disappear() -> None:
    issues = validate_scene_against_survey(_survey(), _scene(pane_layout=None))
    assert any(
        issue.code == "opening_visual_detail_lost"
        and issue.object_id == "front_glazed_door_lower_right"
        and "pane_layout" in issue.message
        for issue in issues
    )


def test_exact_pane_layout_preservation_passes_fidelity_guard() -> None:
    issues = validate_scene_against_survey(_survey(), _scene())
    assert not any(
        issue.code == "opening_visual_detail_lost"
        and issue.object_id == "front_glazed_door_lower_right"
        for issue in issues
    )
