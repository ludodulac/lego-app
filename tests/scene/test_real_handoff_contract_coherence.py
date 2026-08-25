from brickhouse.scene import ArchitecturalScene, SceneSurveySeverity, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SRC = {"kind": "inferred", "confidence": 0.5}
USER = {"kind": "user_provided", "confidence": 1.0}


def _volume():
    return {
        "id": "volume_main",
        "position": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 10, "source": USER},
        "depth": {"value": 8, "source": SRC},
        "height": {"value": 7, "source": SRC},
        "floors": 2,
        "source": SRC,
    }


def test_high_image_mapping_preserves_canonical_left_facade_order() -> None:
    survey = ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "left-order",
        "name": "left order",
        "photos": [
            {
                "photo_index": 1,
                "facade": "left",
                "description": "left",
                "source": USER,
                "image_left_maps_to_facade_offset": "high",
            },
            {"photo_index": 2, "facade": "front", "description": "front", "source": USER},
        ],
        "observations": [
            {
                "id": "image_left",
                "kind": "opening",
                "facade": "left",
                "certainty": "certain",
                "statement": "left image opening",
                "evidence": [{"photo_index": 1, "observation": "visible"}],
                "attributes": {"physical_object_count": 1, "facade_horizontal_rank": 1},
            },
            {
                "id": "image_right",
                "kind": "opening",
                "facade": "left",
                "certainty": "certain",
                "statement": "right image opening",
                "evidence": [{"photo_index": 1, "observation": "visible"}],
                "attributes": {"physical_object_count": 1, "facade_horizontal_rank": 2},
            },
        ],
    })
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "left-order-scene",
        "name": "left order scene",
        "units": "m",
        "volumes": [_volume()],
        "openings": [
            {
                "id": "image_left",
                "type": "unknown",
                "volume_id": "volume_main",
                "facade": "left",
                "offset_horizontal": 5.5,
                "offset_vertical": 3,
                "width": 1,
                "height": 1,
                "source": SRC,
            },
            {
                "id": "image_right",
                "type": "unknown",
                "volume_id": "volume_main",
                "facade": "left",
                "offset_horizontal": 2,
                "offset_vertical": 1,
                "width": 1,
                "height": 1,
                "source": SRC,
            },
        ],
        "appearance": {},
    })
    codes = {issue.code for issue in validate_scene_against_survey(survey, scene)}
    assert "opening_horizontal_order_drift" not in codes


def test_certain_grade_can_remain_metric_unresolved_when_direction_is_only_plausible() -> None:
    survey = ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "terrain-certainty",
        "name": "terrain certainty",
        "photos": [
            {"photo_index": 1, "facade": "right", "description": "right", "source": USER},
            {"photo_index": 2, "facade": "front", "description": "front", "source": USER},
        ],
        "observations": [{
            "id": "terrain_right",
            "kind": "terrain",
            "facade": "right",
            "certainty": "certain",
            "statement": "longitudinal grade is visible",
            "evidence": [{"photo_index": 1, "observation": "grade varies"}],
            "attributes": {"slope_direction": "front_to_rear_up"},
            "attribute_certainty": {"slope_direction": "plausible"},
        }],
    })
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "terrain-scene",
        "name": "terrain scene",
        "units": "m",
        "volumes": [_volume()],
        "terrain": {
            "kind": "facade_grade_profiles",
            "profiles": [{
                "facade": "right",
                "start_elevation": None,
                "end_elevation": None,
                "outward_extent": None,
                "source": {"kind": "observed", "confidence": 0.9},
                "evidence": [{"photo_index": 1, "observation": "grade exists; metric direction unresolved"}],
            }],
        },
        "appearance": {},
    })
    codes = {issue.code for issue in validate_scene_against_survey(survey, scene)}
    assert "scene_grade_not_in_survey" not in codes


def test_part_of_building_boundary_is_preserved_by_scene_volume_ownership() -> None:
    survey = ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "implicit-part-of",
        "name": "implicit part of",
        "photos": [{"photo_index": 1, "facade": "front", "description": "front", "source": USER}],
        "observations": [
            {
                "id": "building_main",
                "kind": "building_boundary",
                "certainty": "certain",
                "statement": "building boundary",
                "evidence": [{"photo_index": 1, "observation": "building"}],
            },
            {
                "id": "front_opening",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "opening",
                "evidence": [{"photo_index": 1, "observation": "embedded"}],
                "attributes": {"physical_object_count": 1},
            },
        ],
        "relations": [{
            "id": "opening_part_of_building",
            "kind": "part_of",
            "subject_id": "front_opening",
            "object_id": "building_main",
            "certainty": "certain",
            "statement": "opening belongs to building",
            "evidence": [{"photo_index": 1, "observation": "embedded"}],
        }],
    })
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "implicit-part-of-scene",
        "name": "implicit part of scene",
        "units": "m",
        "volumes": [_volume()],
        "openings": [{
            "id": "front_opening",
            "type": "unknown",
            "volume_id": "volume_main",
            "facade": "front",
            "offset_horizontal": 1,
            "offset_vertical": 1,
            "width": 1,
            "height": 1,
            "source": SRC,
        }],
        "appearance": {},
    })
    codes = {issue.code for issue in validate_scene_against_survey(survey, scene)}
    assert "certain_relation_missing" not in codes


def test_context_adjacency_is_warning_not_invented_target_geometry() -> None:
    survey = ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "context-relation",
        "name": "context relation",
        "photos": [
            {"photo_index": 1, "facade": "left", "description": "left", "source": USER},
            {"photo_index": 2, "facade": "front", "description": "front", "source": USER},
        ],
        "observations": [
            {
                "id": "building_main",
                "kind": "building_boundary",
                "certainty": "certain",
                "statement": "building",
                "evidence": [{"photo_index": 1, "observation": "building"}],
            },
            {
                "id": "neighbor",
                "kind": "context",
                "facade": "left",
                "certainty": "certain",
                "statement": "neighbor",
                "evidence": [{"photo_index": 1, "observation": "neighbor"}],
            },
        ],
        "relations": [{
            "id": "neighbor_adjacent",
            "kind": "adjacent_to",
            "subject_id": "neighbor",
            "object_id": "building_main",
            "certainty": "certain",
            "statement": "neighbor adjacent",
            "evidence": [{"photo_index": 1, "observation": "adjacent"}],
        }],
    })
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "context-scene",
        "name": "context scene",
        "units": "m",
        "volumes": [_volume()],
        "appearance": {},
    })
    issues = validate_scene_against_survey(survey, scene)
    assert not [issue for issue in issues if issue.severity is SceneSurveySeverity.ERROR]
    assert any(issue.code == "certain_context_relation_scene_unrepresentable" for issue in issues)
