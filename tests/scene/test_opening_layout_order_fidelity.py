from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey(*, horizontal_certainty: str = "certain") -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "opening-order-survey",
        "name": "Opening order survey",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "front",
                "source": {"kind": "user_provided", "confidence": 0.99},
            }
        ],
        "observations": [
            {
                "id": "lower_left",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "lower left window",
                "evidence": [{"photo_index": 1, "observation": "visible"}],
                "attributes": {
                    "physical_object_count": 1,
                    "semantic_type": "window",
                    "facade_horizontal_rank": 1,
                    "facade_vertical_rank": 1,
                },
                "attribute_certainty": {
                    "facade_horizontal_rank": horizontal_certainty,
                    "facade_vertical_rank": "certain",
                },
            },
            {
                "id": "upper_right",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "upper right window",
                "evidence": [{"photo_index": 1, "observation": "visible"}],
                "attributes": {
                    "physical_object_count": 1,
                    "semantic_type": "window",
                    "facade_horizontal_rank": 2,
                    "facade_vertical_rank": 2,
                },
                "attribute_certainty": {
                    "facade_horizontal_rank": horizontal_certainty,
                    "facade_vertical_rank": "certain",
                },
            },
        ],
    })


def _scene(*, swapped_horizontal: bool = False, swapped_vertical: bool = False) -> ArchitecturalScene:
    first_x, second_x = ((7.0, 1.0) if swapped_horizontal else (1.0, 7.0))
    first_z, second_z = ((4.0, 1.0) if swapped_vertical else (1.0, 4.0))
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "opening-order-scene",
        "name": "Opening order scene",
        "units": "m",
        "volumes": [
            {
                "id": "main",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": {"value": 10, "source": SOURCE},
                "depth": {"value": 8, "source": SOURCE},
                "height": {"value": 7, "source": SOURCE},
                "floors": 2,
                "source": SOURCE,
            }
        ],
        "openings": [
            {
                "id": "lower_left",
                "type": "window",
                "volume_id": "main",
                "facade": "front",
                "offset_horizontal": first_x,
                "offset_vertical": first_z,
                "width": 1,
                "height": 1,
                "source": SOURCE,
            },
            {
                "id": "upper_right",
                "type": "window",
                "volume_id": "main",
                "facade": "front",
                "offset_horizontal": second_x,
                "offset_vertical": second_z,
                "width": 1,
                "height": 1,
                "source": SOURCE,
            },
        ],
        "appearance": {"walls": {"color": "white"}, "frames": {"color": "dark_gray"}},
    })


def test_certain_horizontal_ranks_cannot_be_mirrored_in_scene() -> None:
    codes = {
        issue.code
        for issue in validate_scene_against_survey(_survey(), _scene(swapped_horizontal=True))
    }
    assert "opening_horizontal_order_drift" in codes


def test_certain_vertical_ranks_cannot_be_inverted_in_scene() -> None:
    codes = {
        issue.code
        for issue in validate_scene_against_survey(_survey(), _scene(swapped_vertical=True))
    }
    assert "opening_vertical_order_drift" in codes


def test_correct_qualitative_order_does_not_require_exact_metric_spacing() -> None:
    assert validate_scene_against_survey(_survey(), _scene()) == []


def test_plausible_horizontal_rank_is_not_promoted_to_strict_order() -> None:
    codes = {
        issue.code
        for issue in validate_scene_against_survey(
            _survey(horizontal_certainty="plausible"),
            _scene(swapped_horizontal=True),
        )
    }
    assert "opening_horizontal_order_drift" not in codes
