import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_shutters import augment_brick_model_with_scene_shutters
from brickhouse.scene import ArchitecturalScene


FIXTURES = Path(__file__).parent / "fixtures"


def _load_json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _seed_model(scene: ArchitecturalScene) -> BrickModel:
    return BrickModel(
        building_id=scene.id,
        volume_id="volume_main",
        width_studs=48,
        depth_studs=40,
        height_plates=120,
        parts=[BrickModelPart(
            placement_id="seed",
            part_id="BRICK_1X1",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade="front",
        )],
    )


def test_reference_house_shutter_observations_match_known_openings_and_render_only_observed_ids():
    scene_data = _load_json("architectural_scene_real_house_5_v25.json")
    evidence = _load_json("real_house_5_shutter_observations.json")
    openings = {opening["id"]: opening for opening in scene_data["openings"]}

    observed_ids = {item["opening_id"] for item in evidence["observations"]}
    assert observed_ids == {
        "front_upper_left_window",
        "front_upper_right_window",
        "front_middle_right_window",
        "right_upper_window",
    }
    assert {item["opening_id"] for item in evidence["explicit_non_observations"]} == {
        "front_middle_left_window"
    }
    assert observed_ids <= openings.keys()

    by_id = {item["opening_id"]: item for item in evidence["observations"]}
    for opening_id, observation in by_id.items():
        openings[opening_id]["opening_visual"] = {
            "shutter_count": observation["shutter_count"],
            "shutter_style": observation["shutter_style"],
            "shutter_state": observation["shutter_state"],
            "shutter_color": observation["shutter_color"],
        }

    scene = ArchitecturalScene.model_validate(scene_data)
    enriched = augment_brick_model_with_scene_shutters(
        _seed_model(scene), scene, front_width_studs=48
    )
    rendered_ids = {
        part.opening_id
        for part in enriched.parts
        if part.placement_id.startswith("scene-shutter:")
    }
    assert rendered_ids == observed_ids
    assert "front_middle_left_window" not in rendered_ids
