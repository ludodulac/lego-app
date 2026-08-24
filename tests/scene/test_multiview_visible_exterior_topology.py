from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey():
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1", "id": "multiview-exterior", "name": "Multi-view exterior",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "canonical front", "source": SOURCE},
            {"photo_index": 2, "facade": "left", "description": "left view A", "source": SOURCE},
            {"photo_index": 3, "facade": "left", "description": "left view B", "source": SOURCE},
        ],
        "observations": [
            {"id": "terrace", "kind": "platform", "facade": "left", "certainty": "certain",
             "statement": "raised terrace is visible",
             "evidence": [{"photo_index": 2, "observation": "terrace edge and supports visible"}]},
            {"id": "stair_visible", "kind": "stair", "facade": "left", "certainty": "certain",
             "statement": "visible stair run exists",
             "evidence": [{"photo_index": 2, "observation": "lower run visible"}]},
        ],
        "relations": [{
            "id": "stair_terrace_context", "kind": "adjacent_to", "subject_id": "stair_visible", "object_id": "terrace",
            "certainty": "certain", "statement": "second view confirms both belong to the same exterior circulation context",
            "evidence": [{"photo_index": 3, "observation": "terrace and stair are both visible; hidden continuation remains occluded"}],
        }],
    })


def _scene(*, include_stair=False):
    stairs = []
    if include_stair:
        stairs = [{
            "id": "stair_visible", "start": {"x": -1, "y": 1, "z": 0}, "end": {"x": -1, "y": 3, "z": 1.4},
            "width": 1, "material": "concrete", "source": SOURCE,
        }]
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2", "id": "scene", "name": "scene", "units": "m",
        "volumes": [{"id": "main", "position": {"x": 0, "y": 0, "z": 0},
                     "width": {"value": 10, "source": SOURCE}, "depth": {"value": 8, "source": SOURCE},
                     "height": {"value": 6, "source": SOURCE}, "floors": 2, "source": SOURCE}],
        "platforms": [{"id": "terrace", "position": {"x": -2, "y": 3, "z": 1.4}, "width": 2, "depth": 3,
                       "thickness": .2, "material": "timber", "source": SOURCE}],
        "stairs": stairs,
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
    })


def test_multiview_certain_visible_stair_cannot_be_dropped_because_continuation_is_hidden():
    issues = validate_scene_against_survey(_survey(), _scene())
    codes = {issue.code for issue in issues}
    assert "certain_multiview_stair_not_geometrically_encoded" in codes


def test_visible_stair_primitive_satisfies_multiview_guard_without_inventing_hidden_connection():
    issues = validate_scene_against_survey(_survey(), _scene(include_stair=True))
    codes = {issue.code for issue in issues}
    assert "certain_multiview_stair_not_geometrically_encoded" not in codes
    assert "certain_connection_broken" not in codes
