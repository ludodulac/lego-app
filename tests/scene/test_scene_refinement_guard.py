from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "refined-exterior-survey",
        "name": "Refined exterior survey",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "canonical front", "source": SOURCE},
            {"photo_index": 2, "facade": "left", "description": "first side view", "source": SOURCE},
            {"photo_index": 3, "facade": "left", "description": "targeted side refinement", "source": SOURCE},
        ],
        "observations": [
            {
                "id": "landing-hypothesis",
                "kind": "platform",
                "facade": "left",
                "certainty": "plausible",
                "statement": "A landing-like surface may continue behind the wall.",
                "evidence": [{"photo_index": 2, "observation": "Only part of the horizontal surface is visible."}],
            },
            {
                "id": "landing-refined",
                "kind": "platform",
                "facade": "left",
                "certainty": "certain",
                "statement": "The targeted angle shows the actual landing footprint.",
                "evidence": [{"photo_index": 3, "observation": "Both landing edges are visible."}],
                "attributes": {"refines_observation_id": "landing-hypothesis"},
            },
        ],
    })


def _scene(ids: list[str]) -> ArchitecturalScene:
    platforms = []
    for index, item_id in enumerate(ids):
        platforms.append({
            "id": item_id,
            "host_volume_id": "main",
            "position": {"x": -1.0, "y": 2.0 + index * 2.0, "z": 1.2},
            "width": 1.0,
            "depth": 1.2,
            "thickness": 0.2,
            "material": "concrete",
            "source": {"kind": "inferred", "confidence": 0.6 if item_id == "landing-hypothesis" else 0.9},
        })
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "refined-exterior-scene",
        "name": "Refined exterior scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 8, "source": SOURCE},
            "depth": {"value": 6, "source": SOURCE},
            "height": {"value": 5, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": platforms,
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
    })


def test_scene_must_use_terminal_refinement_not_old_hypothesis() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene(["landing-hypothesis"]))}
    assert "superseded_platform_rendered" in codes


def test_scene_cannot_render_old_and_refined_platform_as_two_objects() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(),
        _scene(["landing-hypothesis", "landing-refined"]),
    )}
    assert "superseded_platform_rendered" in codes


def test_terminal_refinement_alone_is_allowed() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(), _scene(["landing-refined"]))}
    assert "superseded_platform_rendered" not in codes
    assert "scene_platform_not_in_survey" not in codes
