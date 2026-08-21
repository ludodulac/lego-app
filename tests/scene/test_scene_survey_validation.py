from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


def survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey_test",
        "name": "Survey test",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": {"kind": "user_provided", "confidence": 0.99}, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 2, "facade": "right", "description": "right", "source": {"kind": "user_provided", "confidence": 0.99}, "image_left_maps_to_facade_offset": "low"},
        ],
        "observations": [
            {"id": "front_window", "kind": "opening", "facade": "front", "certainty": "certain", "statement": "window", "evidence": [{"photo_index": 1, "observation": "visible"}], "attributes": {"semantic_type": "window"}},
            {"id": "right_workshop", "kind": "opening", "facade": "right", "certainty": "certain", "statement": "workshop", "evidence": [{"photo_index": 2, "observation": "visible"}], "attributes": {"semantic_type": "window", "user_confirmed_identity": "workshop_window"}},
            {"id": "right_false", "kind": "opening", "facade": "right", "certainty": "unproven", "statement": "uncertain", "evidence": [{"photo_index": 2, "observation": "beyond boundary"}], "attributes": {"semantic_type": "window_unconfirmed"}},
            {"id": "right_grade", "kind": "terrain", "facade": "right", "certainty": "certain", "statement": "road rises", "evidence": [{"photo_index": 2, "observation": "rising road"}], "attributes": {"slope_direction": "front_to_rear_upward"}},
            {"id": "front_roof", "kind": "roof", "facade": "front", "certainty": "certain", "statement": "front gable", "evidence": [{"photo_index": 1, "observation": "gable"}], "attributes": {"front_is_gable": True}},
            {"id": "chimney", "kind": "chimney", "facade": "front", "certainty": "certain", "statement": "chimney", "evidence": [{"photo_index": 1, "observation": "visible"}]},
        ],
    })


def scene(*, include_false: bool = False, workshop_type: str = "window") -> ArchitecturalScene:
    openings = [
        {"id": "front_window", "type": "window", "volume_id": "volume_main", "facade": "front", "offset_horizontal": 1.0, "offset_vertical": 1.0, "width": 1.0, "height": 1.0, "source": {"kind": "inferred", "confidence": 0.6}},
        {"id": "right_workshop", "type": workshop_type, "volume_id": "volume_main", "facade": "right", "offset_horizontal": 5.0, "offset_vertical": 0.5, "width": 1.0, "height": 1.0, "source": {"kind": "inferred", "confidence": 0.6}},
    ]
    if include_false:
        openings.append({"id": "right_false", "type": "window", "volume_id": "volume_main", "facade": "right", "offset_horizontal": 7.0, "offset_vertical": 3.0, "width": 1.0, "height": 1.0, "source": {"kind": "inferred", "confidence": 0.3}})
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene_test",
        "name": "Scene test",
        "units": "m",
        "volumes": [{"id": "volume_main", "position": {"x": 0, "y": 0, "z": 0}, "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 0.99}}, "depth": {"value": 9, "source": {"kind": "inferred", "confidence": 0.5}}, "height": {"value": 7, "source": {"kind": "inferred", "confidence": 0.5}}, "floors": 3, "source": {"kind": "inferred", "confidence": 0.6}}],
        "openings": openings,
        "roofs": [{"id": "roof", "volume_id": "volume_main", "type": "gable", "overhang": 0.3, "ridge_direction": "depth", "pitch_degrees": 20, "source": {"kind": "inferred", "confidence": 0.5}}],
        "terrain": {"kind": "facade_grade_profiles", "profiles": [{"facade": "right", "start_elevation": 0, "end_elevation": 1.5, "source": {"kind": "inferred", "confidence": 0.5}}]},
        "chimneys": [{"id": "chimney_scene", "position": {"x": 1, "y": 2, "z": 7}, "width": 0.7, "depth": 0.6, "height": 1.2, "source": {"kind": "inferred", "confidence": 0.4}}],
        "visibility": [{"facade": "front", "spans": [{"from": 0, "to": 10, "state": "visible"}]}, {"facade": "right", "spans": [{"from": 0, "to": 9, "state": "visible"}]}, {"facade": "left", "spans": [{"from": 0, "to": 9, "state": "unknown"}]}, {"facade": "rear", "spans": [{"from": 0, "to": 10, "state": "unknown"}]}],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_valid_scene_preserves_survey_semantics() -> None:
    assert validate_scene_against_survey(survey(), scene()) == []


def test_unproven_opening_cannot_be_promoted() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(survey(), scene(include_false=True))}
    assert "unproven_opening_promoted" in codes


def test_user_confirmed_window_type_cannot_drift() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(survey(), scene(workshop_type="door"))}
    assert "opening_type_drift" in codes
