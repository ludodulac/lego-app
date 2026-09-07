from copy import deepcopy

import pytest
from pydantic import ValidationError

from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.models import CONNECTIVITY_TOLERANCE_M
from brickhouse.scene.stair_contact import closest_stair_run_endpoint_contact


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _payload(run_a, run_b, *, relation=None):
    data = {
        "schema_version": "0.2",
        "id": "native-stair-contact",
        "name": "Native stair contact",
        "units": "m",
        "volumes": [{
            "id": "host",
            "position": {"x": run_b[1]["x"], "y": run_b[1]["y"], "z": 0},
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
        "appearance": {"walls": {"color": "off_white"}},
    }
    if relation is not None:
        data["relations"] = [relation]
    return data


def _touching_runs():
    return (
        ({"x": 0, "y": 0, "z": 0}, {"x": 1, "y": 0, "z": 1}),
        ({"x": 1, "y": 0, "z": 1}, {"x": 1, "y": 1, "z": 2}),
    )


def test_touching_stair_runs_are_native_connectivity_without_semantic_relation():
    run_a, run_b = _touching_runs()
    scene = ArchitecturalScene.model_validate(_payload(run_a, run_b))

    assert scene.relations == []
    contact = closest_stair_run_endpoint_contact(scene.stairs[0], scene.stairs[1])
    assert contact is not None
    assert contact.first_endpoint == "end"
    assert contact.second_endpoint == "start"
    assert contact.horizontal_gap == 0
    assert contact.vertical_gap == 0


def test_endpoint_gap_outside_canonical_tolerance_is_not_contact():
    delta = CONNECTIVITY_TOLERANCE_M * 1.1
    run_a = ({"x": 0, "y": 0, "z": 0}, {"x": 1, "y": 0, "z": 1})
    run_b = (
        {"x": 1 + delta, "y": 0, "z": 1},
        {"x": 1 + delta, "y": 1, "z": 2},
    )

    with pytest.raises(ValidationError, match="does not connect to ground, a platform, or the building"):
        ArchitecturalScene.model_validate(_payload(run_a, run_b))


def test_resolved_stair_to_stair_connects_to_requires_endpoint_contact():
    run_a, run_b = _touching_runs()
    relation = {
        "id": "run-junction",
        "kind": "connects_to",
        "subject_id": "run-a",
        "object_id": "run-b",
        "certainty": "certain",
        "geometry_status": "resolved",
        "statement": "the two stair runs meet",
    }
    scene = ArchitecturalScene.model_validate(_payload(run_a, run_b, relation=relation))
    assert scene.relations[0].geometry_status == "resolved"

    delta = CONNECTIVITY_TOLERANCE_M * 1.1
    disconnected_b = (
        {"x": 1 + delta, "y": 0, "z": 1},
        {"x": 1 + delta, "y": 1, "z": 2},
    )
    with pytest.raises(ValidationError, match="resolved scene relation 'run-junction' connects_to"):
        ArchitecturalScene.model_validate(_payload(run_a, disconnected_b, relation=relation))


def test_crossing_corridors_without_endpoint_contact_do_not_connect_runs():
    run_a = ({"x": 0, "y": 0, "z": 0}, {"x": 2, "y": 0, "z": 1})
    run_b = ({"x": 1, "y": -1, "z": 0.5}, {"x": 1, "y": 1, "z": 1.5})
    # The two centerlines cross in XY, but no explicit endpoints meet.
    with pytest.raises(ValidationError, match="does not connect to ground, a platform, or the building"):
        ArchitecturalScene.model_validate(_payload(run_a, run_b))


def test_contact_analysis_does_not_mutate_stair_runs():
    run_a, run_b = _touching_runs()
    scene = ArchitecturalScene.model_validate(_payload(run_a, run_b))
    before = deepcopy(scene.model_dump())

    closest_stair_run_endpoint_contact(scene.stairs[0], scene.stairs[1])

    assert scene.model_dump() == before
