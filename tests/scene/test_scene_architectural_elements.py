from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey_elements",
        "name": "Survey elements",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": {"kind": "user_provided", "confidence": 0.99}},
            {"photo_index": 2, "facade": "left", "description": "left", "source": {"kind": "user_provided", "confidence": 0.99}},
        ],
        "known_measurements": [{"kind": "front_width", "value": 10.0, "units": "m", "source": {"kind": "user_provided", "confidence": 0.99}}],
        "observations": [
            {"id": "rear_deck_01", "kind": "platform", "facade": "left", "certainty": "certain", "statement": "deck", "evidence": [{"photo_index": 2, "observation": "visible"}], "attributes": {"architectural_kind": "platform", "target_building_ownership": "proven"}},
            {"id": "left_exterior_stair_01", "kind": "stair", "facade": "left", "certainty": "certain", "statement": "stair", "evidence": [{"photo_index": 2, "observation": "visible"}], "attributes": {"architectural_kind": "stair", "target_building_ownership": "proven"}},
            {"id": "left_low_attached_volume_01", "kind": "volume", "facade": "left", "certainty": "certain", "statement": "attached volume", "evidence": [{"photo_index": 2, "observation": "visible"}], "attributes": {"architectural_kind": "volume", "target_building_ownership": "proven"}},
        ],
    })


def _scene(include_elements: bool) -> ArchitecturalScene:
    volumes = [{"id": "volume_main", "position": {"x": 0, "y": 0, "z": 0}, "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 0.99}}, "depth": {"value": 9, "source": {"kind": "inferred", "confidence": 0.5}}, "height": {"value": 7, "source": {"kind": "inferred", "confidence": 0.5}}, "floors": 3, "source": {"kind": "inferred", "confidence": 0.6}}]
    platforms = []
    stairs = []
    if include_elements:
        volumes.append({"id": "left_low_attached_volume_01", "position": {"x": 0, "y": 4, "z": 0}, "width": {"value": 3, "source": {"kind": "inferred", "confidence": 0.5}}, "depth": {"value": 2, "source": {"kind": "inferred", "confidence": 0.5}}, "height": {"value": 2, "source": {"kind": "inferred", "confidence": 0.5}}, "floors": 1, "source": {"kind": "inferred", "confidence": 0.5}})
        platforms.append({"id": "rear_deck_01", "position": {"x": 0, "y": 7, "z": 1}, "width": 3, "depth": 2, "thickness": 0.2, "source": {"kind": "inferred", "confidence": 0.5}})
        stairs.append({"id": "left_exterior_stair_01", "start": {"x": 0, "y": 5, "z": 0}, "end": {"x": 0, "y": 7, "z": 1}, "width": 1, "source": {"kind": "inferred", "confidence": 0.5}})
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene_elements",
        "name": "Scene elements",
        "units": "m",
        "volumes": volumes,
        "platforms": platforms,
        "stairs": stairs,
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_scene_preserves_certain_architectural_elements_by_id() -> None:
    assert validate_scene_against_survey(_survey(), _scene(include_elements=True)) == []


def test_scene_rejects_loss_of_certain_architectural_elements() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene(include_elements=False))}
    assert {"certain_volume_missing", "certain_platform_missing", "certain_stair_missing"} <= codes
