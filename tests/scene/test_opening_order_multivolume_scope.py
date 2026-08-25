from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SRC = {"kind": "inferred", "confidence": 0.5}
USER = {"kind": "user_provided", "confidence": 1.0}


def test_horizontal_ranks_are_not_compared_across_different_scene_volumes() -> None:
    survey = ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "multi-volume-order",
        "name": "multi volume order",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": USER},
            {
                "photo_index": 2,
                "facade": "left",
                "description": "left",
                "source": USER,
                "image_left_maps_to_facade_offset": "high",
            },
        ],
        "observations": [
            {
                "id": "main_left_opening",
                "kind": "opening",
                "facade": "left",
                "certainty": "certain",
                "statement": "opening on main volume",
                "evidence": [{"photo_index": 2, "observation": "visible"}],
                "attributes": {"physical_object_count": 1, "facade_horizontal_rank": 2},
            },
            {
                "id": "secondary_left_opening",
                "kind": "opening",
                "facade": "left",
                "certainty": "certain",
                "statement": "opening on secondary volume",
                "evidence": [{"photo_index": 2, "observation": "visible"}],
                "attributes": {"physical_object_count": 1, "facade_horizontal_rank": 1},
            },
        ],
    })
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "multi-volume-order-scene",
        "name": "multi volume order scene",
        "units": "m",
        "volumes": [
            {
                "id": "main",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": {"value": 10, "source": USER},
                "depth": {"value": 8, "source": SRC},
                "height": {"value": 7, "source": SRC},
                "floors": 2,
                "source": SRC,
            },
            {
                "id": "secondary",
                "position": {"x": -2, "y": 5, "z": 0},
                "width": {"value": 2, "source": SRC},
                "depth": {"value": 2, "source": SRC},
                "height": {"value": 2, "source": SRC},
                "floors": 1,
                "source": SRC,
            },
        ],
        "openings": [
            {
                "id": "main_left_opening",
                "type": "unknown",
                "volume_id": "main",
                "facade": "left",
                "offset_horizontal": 2.5,
                "offset_vertical": 1,
                "width": 1,
                "height": 1,
                "source": SRC,
            },
            {
                "id": "secondary_left_opening",
                "type": "unknown",
                "volume_id": "secondary",
                "facade": "left",
                "offset_horizontal": 0.2,
                "offset_vertical": 0.2,
                "width": 1,
                "height": 1,
                "source": SRC,
            },
        ],
        "appearance": {},
    })
    codes = {issue.code for issue in validate_scene_against_survey(survey, scene)}
    assert "opening_horizontal_order_drift" not in codes
