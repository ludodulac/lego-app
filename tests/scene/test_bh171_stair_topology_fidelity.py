from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey(*, certainty="certain", component_run_ids=None):
    topology = {
        "minimum_run_count": 2,
        "direction_change": True,
        "turning_node_kind": "turn_or_landing",
    }
    observations = [{
        "id": "stair-system",
        "kind": "stair",
        "certainty": "certain",
        "statement": "exterior stair system changes direction",
        "evidence": [{"photo_index": 2, "observation": "two connected stair portions with a turn are visible"}],
        "attributes": {"stair_topology": topology},
        "attribute_certainty": {"stair_topology": certainty},
    }]
    if component_run_ids is not None:
        topology["component_run_ids"] = component_run_ids
        observations.extend({
            "id": run_id,
            "kind": "stair",
            "certainty": "certain",
            "statement": f"visible component run {run_id}",
            "evidence": [{"photo_index": 2, "observation": f"{run_id} visible"}],
        } for run_id in component_run_ids)
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "stair-survey",
        "name": "Stair survey",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "front reference",
            "source": SOURCE,
        }, {
            "photo_index": 2,
            "facade": "rear",
            "description": "rear stair view",
            "source": SOURCE,
        }],
        "observations": observations,
    })


def _scene(*, stair_ids=()):
    stairs = []
    for index, stair_id in enumerate(stair_ids):
        stairs.append({
            "id": stair_id,
            "start": {"x": float(index), "y": 0.0, "z": float(index)},
            "end": {"x": float(index + 1), "y": 0.0, "z": float(index + 1)},
            "width": 1.0,
            "source": SOURCE,
        })
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "stair-scene",
        "name": "Stair scene",
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
        "stairs": stairs,
        "appearance": {"walls": {"color": "off_white"}},
    })


def _codes(survey, scene):
    return {issue.code for issue in validate_scene_against_survey(survey, scene)}


def test_certain_multirun_topology_cannot_be_collapsed_into_one_metric_stairrun():
    codes = _codes(_survey(), _scene(stair_ids=("stair-system",)))

    assert "multi_run_stair_topology_unresolved" in codes


def test_unresolved_topology_gate_does_not_invent_component_coordinates():
    survey = _survey()
    scene = _scene()
    before = scene.model_dump()

    validate_scene_against_survey(survey, scene)

    assert scene.model_dump() == before
    assert scene.stairs == []


def test_plausible_multirun_topology_is_preserved_without_becoming_hard_metric_gate():
    codes = _codes(_survey(certainty="plausible"), _scene(stair_ids=("stair-system",)))

    assert "multi_run_stair_topology_unresolved" not in codes


def test_evidenced_component_ids_satisfy_noncollapse_gate_when_all_are_metrified():
    survey = _survey(component_run_ids=["run-a", "run-b"])
    codes = _codes(survey, _scene(stair_ids=("run-a", "run-b")))

    assert "multi_run_stair_topology_unresolved" not in codes
    assert "multi_run_stair_component_lost" not in codes


def test_missing_evidenced_component_run_is_a_fidelity_error():
    survey = _survey(component_run_ids=["run-a", "run-b"])
    codes = _codes(survey, _scene(stair_ids=("run-a",)))

    assert "multi_run_stair_component_lost" in codes
