from copy import deepcopy

from brickhouse.scene import (
    ArchitecturalScene,
    analyze_multi_run_stair_geometry,
    validate_scene_against_survey,
)
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _survey(*, direction_change=True):
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "multi-run-survey",
        "name": "Multi-run stair survey",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "view establishing a multi-run exterior stair",
            "source": SOURCE,
            "image_left_maps_to_facade_offset": "low",
        }],
        "observations": [
            {
                "id": "stair-system",
                "kind": "stair",
                "facade": "front",
                "certainty": "certain",
                "statement": "exterior stair system with connected runs",
                "evidence": [{"photo_index": 1, "observation": "stair system visible"}],
                "attributes": {
                    "stair_topology": {
                        "minimum_run_count": 2,
                        "direction_change": direction_change,
                        "turning_node_kind": "turn_or_landing" if direction_change else None,
                        "component_run_ids": ["run-a", "run-b"],
                    }
                },
                "attribute_certainty": {"stair_topology": "certain"},
            },
            {
                "id": "run-a",
                "kind": "stair",
                "facade": "front",
                "certainty": "certain",
                "statement": "first stair run",
                "evidence": [{"photo_index": 1, "observation": "first run visible"}],
            },
            {
                "id": "run-b",
                "kind": "stair",
                "facade": "front",
                "certainty": "certain",
                "statement": "second stair run",
                "evidence": [{"photo_index": 1, "observation": "second run visible"}],
            },
        ],
    })


def _scene(run_a, run_b, *, host_point):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "multi-run-scene",
        "name": "Multi-run stair scene",
        "units": "m",
        "volumes": [{
            "id": "host",
            "position": {"x": host_point[0], "y": host_point[1], "z": 0},
            "width": {"value": 2, "source": SOURCE},
            "depth": {"value": 2, "source": SOURCE},
            "height": {"value": 4, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "stairs": [
            {"id": "run-a", "start": run_a[0], "end": run_a[1], "width": 1.0, "source": SOURCE},
            {"id": "run-b", "start": run_b[0], "end": run_b[1], "width": 1.0, "source": SOURCE},
        ],
        # The legacy Scene connectivity validator does not yet treat StairRun ↔
        # StairRun endpoint contact as an external anchor. Keep the semantic
        # junction explicitly unresolved there; BH-174 independently verifies
        # whether the two metric runs actually meet.
        "relations": [
            {
                "id": "run-a-system",
                "kind": "connects_to",
                "subject_id": "run-a",
                "object_id": "stair-system",
                "certainty": "certain",
                "geometry_status": "unresolved",
                "statement": "run-a belongs to the stair system",
            },
            {
                "id": "run-b-system",
                "kind": "connects_to",
                "subject_id": "run-b",
                "object_id": "stair-system",
                "certainty": "certain",
                "geometry_status": "unresolved",
                "statement": "run-b belongs to the stair system",
            },
        ],
        "appearance": {"walls": {"color": "off_white"}},
    })


def _codes(survey, scene):
    return {issue.code for issue in validate_scene_against_survey(survey, scene)}


def test_connected_turning_runs_realize_certain_direction_change():
    survey = _survey()
    scene = _scene(
        ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1}),
        ({"x": 2, "y": 0, "z": 1}, {"x": 2, "y": 2, "z": 2}),
        host_point=(2, 2),
    )

    report = analyze_multi_run_stair_geometry(survey, scene)
    fact = report.facts[0]

    assert fact.connected is True
    assert fact.spanning_path_exists is True
    assert fact.direction_change_realized is True
    assert "multi_run_stair_components_disconnected" not in _codes(survey, scene)
    assert "multi_run_stair_direction_change_not_realized" not in _codes(survey, scene)


def test_disconnected_component_runs_are_fidelity_error():
    survey = _survey()
    scene = _scene(
        ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1}),
        ({"x": 2.5, "y": 0, "z": 1}, {"x": 2.5, "y": 2, "z": 2}),
        host_point=(2.5, 2),
    )

    assert "multi_run_stair_components_disconnected" in _codes(survey, scene)


def test_multiple_collinear_runs_do_not_fake_a_certain_turn():
    survey = _survey()
    scene = _scene(
        ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1}),
        ({"x": 2, "y": 0, "z": 1}, {"x": 4, "y": 0, "z": 2}),
        host_point=(4, 0),
    )

    assert "multi_run_stair_direction_change_not_realized" in _codes(survey, scene)


def test_reversing_component_endpoint_serialization_does_not_break_junction_or_turn():
    survey = _survey()
    scene = _scene(
        ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1}),
        ({"x": 2, "y": 2, "z": 2}, {"x": 2, "y": 0, "z": 1}),
        host_point=(2, 2),
    )

    fact = analyze_multi_run_stair_geometry(survey, scene).facts[0]
    assert fact.connected is True
    assert fact.direction_change_realized is True


def test_degenerate_horizontal_run_keeps_direction_change_unresolved():
    survey = _survey()
    scene = _scene(
        ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1}),
        ({"x": 2, "y": 0, "z": 1}, {"x": 2, "y": 0, "z": 2}),
        host_point=(2, 0),
    )

    fact = analyze_multi_run_stair_geometry(survey, scene).facts[0]
    assert fact.direction_change_realized is None
    assert fact.degenerate_run_ids == ["run-b"]
    assert "multi_run_stair_direction_change_unresolved" in _codes(survey, scene)


def test_geometry_analysis_and_fidelity_do_not_mutate_inputs():
    survey = _survey()
    scene = _scene(
        ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1}),
        ({"x": 2, "y": 0, "z": 1}, {"x": 2, "y": 2, "z": 2}),
        host_point=(2, 2),
    )
    survey_before = deepcopy(survey.model_dump())
    scene_before = deepcopy(scene.model_dump())

    analyze_multi_run_stair_geometry(survey, scene)
    validate_scene_against_survey(survey, scene)

    assert survey.model_dump() == survey_before
    assert scene.model_dump() == scene_before
