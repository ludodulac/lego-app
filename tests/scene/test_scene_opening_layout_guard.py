from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.8}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "opening-layout-survey",
        "name": "Opening layout survey",
        "photos": [{"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE}],
        "observations": [
            {
                "id": "upper-left",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "upper left window",
                "evidence": [{"photo_index": 1, "observation": "upper-left window visible"}],
                "attributes": {"semantic_type": "window", "facade_horizontal_rank": 1, "facade_vertical_rank": 2},
            },
            {
                "id": "upper-right",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "upper right window",
                "evidence": [{"photo_index": 1, "observation": "upper-right window visible"}],
                "attributes": {"semantic_type": "window", "facade_horizontal_rank": 2, "facade_vertical_rank": 2},
            },
            {
                "id": "lower-left",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "lower left window",
                "evidence": [{"photo_index": 1, "observation": "lower-left window visible"}],
                "attributes": {"semantic_type": "window", "facade_horizontal_rank": 1, "facade_vertical_rank": 1},
            },
            {
                "id": "lower-right",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "lower right window",
                "evidence": [{"photo_index": 1, "observation": "lower-right window visible"}],
                "attributes": {"semantic_type": "window", "facade_horizontal_rank": 2, "facade_vertical_rank": 1},
            },
        ],
    })


def _scene(*, mirror=False, swap_levels=False) -> ArchitecturalScene:
    x_left, x_right = (6.5, 1.5) if mirror else (1.5, 6.5)
    z_low, z_high = (4.0, 1.0) if swap_levels else (1.0, 4.0)
    openings = [
        ("upper-left", x_left, z_high),
        ("upper-right", x_right, z_high),
        ("lower-left", x_left, z_low),
        ("lower-right", x_right, z_low),
    ]
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "opening-layout-scene",
        "name": "Opening layout scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 7, "source": SOURCE},
            "height": {"value": 7, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "openings": [
            {
                "id": opening_id,
                "type": "window",
                "volume_id": "main",
                "facade": "front",
                "offset_horizontal": x,
                "offset_vertical": z,
                "width": 1.2,
                "height": 1.4,
                "source": SOURCE,
            }
            for opening_id, x, z in openings
        ],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
    })


def test_correct_qualitative_opening_layout_is_accepted() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene())}
    assert "opening_horizontal_order_drift" not in codes
    assert "opening_vertical_order_drift" not in codes


def test_horizontal_mirror_is_rejected_even_when_opening_count_is_correct() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene(mirror=True))}
    assert "opening_horizontal_order_drift" in codes
    assert "facade_opening_count_drift" not in codes


def test_vertical_row_swap_is_rejected_even_when_opening_count_is_correct() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene(swap_levels=True))}
    assert "opening_vertical_order_drift" in codes
    assert "facade_opening_count_drift" not in codes
