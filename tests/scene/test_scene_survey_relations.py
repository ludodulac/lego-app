from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.7}
PHOTO_SOURCE = {"kind": "user_provided", "confidence": 1.0}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey_relations",
        "name": "Relations",
        "photos": [
            {"photo_index": 1, "facade": "left", "description": "left", "source": PHOTO_SOURCE},
            {"photo_index": 2, "facade": "front", "description": "canonical front", "source": PHOTO_SOURCE},
        ],
        "observations": [
            {"id": "stair_01", "kind": "stair", "facade": "left", "certainty": "certain", "statement": "volée", "evidence": [{"photo_index": 1, "observation": "visible"}]},
            {"id": "landing_01", "kind": "platform", "facade": "left", "certainty": "certain", "statement": "palier", "evidence": [{"photo_index": 1, "observation": "visible"}]},
        ],
        "relations": [{
            "id": "stair_to_landing",
            "kind": "connects_to",
            "subject_id": "stair_01",
            "object_id": "landing_01",
            "certainty": "certain",
            "statement": "La volée rejoint le palier.",
            "evidence": [{"photo_index": 1, "observation": "Les marches aboutissent au palier."}],
        }],
    })


def _scene(stair_end_x: float) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene_relations",
        "name": "Relations",
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
        "platforms": [{"id": "landing_01", "position": {"x": -2, "y": 6, "z": 1}, "width": 2, "depth": 2, "thickness": 0.2, "source": SOURCE}],
        "stairs": [{"id": "stair_01", "start": {"x": -1, "y": 4, "z": 0}, "end": {"x": stair_end_x, "y": 6.5, "z": 1}, "width": 1, "source": SOURCE}],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_certain_survey_connection_is_preserved_when_geometry_touches():
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene(-1.0))}
    assert "certain_connection_broken" not in codes


def test_certain_survey_connection_rejects_disconnected_geometry():
    # Keep the stair endpoint connected to the building boundary so Scene shape
    # validation passes, but break the explicit Survey stair->landing relation.
    scene = ArchitecturalScene.model_validate({
        **_scene(-1.0).model_dump(mode="json"),
        "stairs": [{"id": "stair_01", "start": {"x": -1, "y": 4, "z": 0}, "end": {"x": 0, "y": 4, "z": 1}, "width": 1, "source": SOURCE}],
    })
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), scene)}
    assert "certain_connection_broken" in codes
