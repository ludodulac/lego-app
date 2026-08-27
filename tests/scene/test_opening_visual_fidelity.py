from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "opening_visual_survey",
        "name": "Opening visual survey",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "front",
            "source": {"kind": "user_provided", "confidence": 0.99},
            "image_left_maps_to_facade_offset": "low",
        }],
        "observations": [{
            "id": "front_window",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "Window with visible stone surround, sill and shutters",
            "evidence": [{"photo_index": 1, "observation": "Surround, sill and shutters visible"}],
            "attributes": {"semantic_type": "window", "physical_object_count": 1},
            "opening_visual": {
                "frame_color": "dark_brown",
                "leaf_count": 2,
                "pane_count": 4,
                "mullion_count": 1,
                "glazing": "clear",
                "sill": "projecting",
                "surround_material": "stone_like",
                "surround_color": "light_beige",
                "shutter_count": 2,
                "shutter_style": "folding",
                "shutter_color": "white",
            },
        }],
    })


def _scene(*, has_sill=None, has_decorative_surround=None, opening_visual=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "opening_visual_scene",
        "name": "Opening visual scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "inferred", "confidence": 0.7}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": 0.6}},
            "height": {"value": 6, "source": {"kind": "inferred", "confidence": 0.6}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": 0.6},
        }],
        "openings": [{
            "id": "front_window",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2,
            "offset_vertical": 2,
            "width": 1.4,
            "height": 1.5,
            "source": {"kind": "inferred", "confidence": 0.6},
            "has_sill": has_sill,
            "has_decorative_surround": has_decorative_surround,
            "opening_visual": opening_visual,
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })


def test_observed_sill_and_surround_cannot_disappear_in_scene() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene())}
    assert "opening_sill_lost" in codes
    assert "opening_surround_lost" in codes


def test_observed_pane_and_shutter_composition_cannot_disappear_in_scene() -> None:
    partial = {
        "frame_color": "dark_brown",
        "leaf_count": 2,
        "mullion_count": 1,
        "glazing": "clear",
        "sill": "projecting",
        "surround_material": "stone_like",
        "surround_color": "light_beige",
    }
    issues = validate_scene_against_survey(
        _survey(),
        _scene(has_sill=True, has_decorative_surround=True, opening_visual=partial),
    )
    assert any(
        issue.code == "opening_visual_detail_lost" and "pane_count" in issue.message
        for issue in issues
    )
    assert any(
        issue.code == "opening_visual_detail_lost" and "shutter_count" in issue.message
        for issue in issues
    )


def test_observed_sill_surround_and_composition_are_preserved_exactly() -> None:
    visual = _survey().observations[0].opening_visual.model_dump(mode="json")
    codes = {
        issue.code
        for issue in validate_scene_against_survey(
            _survey(),
            _scene(
                has_sill=True,
                has_decorative_surround=True,
                opening_visual=visual,
            ),
        )
    }
    assert "opening_sill_lost" not in codes
    assert "opening_surround_lost" not in codes
    assert "opening_visual_detail_lost" not in codes
