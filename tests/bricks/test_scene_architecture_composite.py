from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


def _base_model() -> BrickModel:
    return BrickModel(
        building_id="house",
        volume_id="volume_main",
        width_studs=48,
        depth_studs=48,
        height_plates=60,
        parts=[
            BrickModelPart(
                placement_id="wall-1",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            )
        ],
    )


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "house",
        "name": "Composite exterior architecture",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 10, "source": {"kind": "inferred", "confidence": .5}},
            "height": {"value": 7, "source": {"kind": "inferred", "confidence": .5}},
            "floors": 3,
            "source": {"kind": "inferred", "confidence": .6},
        }],
        "platforms": [
            {
                "id": "stair_landing_concrete_01",
                "position": {"x": -1.2, "y": 8.3, "z": 1.2},
                "width": 1.2,
                "depth": 1.3,
                "thickness": .25,
                "source": {"kind": "inferred", "confidence": .6},
                "evidence": [{"photo_index": 1, "observation": "palier maçonné en béton avec muret"}],
            },
            {
                "id": "terrace_timber_01",
                "position": {"x": -2.5, "y": 3.0, "z": 2.4},
                "width": 2.5,
                "depth": 5.3,
                "thickness": .2,
                "source": {"kind": "inferred", "confidence": .6},
                "evidence": [{"photo_index": 2, "observation": "grande terrasse en bois sur poteaux"}],
            },
        ],
        "stairs": [
            {
                "id": "stair_run_concrete_01",
                "start": {"x": -1.0, "y": 7.0, "z": 0},
                "end": {"x": -1.0, "y": 8.3, "z": 1.2},
                "width": 1.1,
                "source": {"kind": "inferred", "confidence": .6},
                "evidence": [{"photo_index": 1, "observation": "première volée maçonnée avec rampes béton"}],
            },
            {
                "id": "stair_run_concrete_02",
                "start": {"x": -1.0, "y": 8.3, "z": 1.2},
                "end": {"x": -1.0, "y": 7.2, "z": 2.4},
                "width": 1.1,
                "source": {"kind": "inferred", "confidence": .6},
                "evidence": [{"photo_index": 2, "observation": "seconde volée maçonnée retournant vers la terrasse"}],
            },
        ],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
        "notes": "Escalier béton en deux volées avec palier; terrasse bois distincte.",
    })


def test_composite_stair_runs_and_timber_deck_survive_to_brick_model() -> None:
    model = augment_brick_model_with_scene_architecture(_base_model(), _scene(), front_width_studs=48)
    ids = [part.placement_id for part in model.parts]

    assert any(value.startswith("scene-stair:stair_run_concrete_01:body:") for value in ids)
    assert any(value.startswith("scene-stair:stair_run_concrete_01:sidewall:") for value in ids)
    assert any(value.startswith("scene-stair:stair_run_concrete_02:body:") for value in ids)
    assert any(value.startswith("scene-platform:stair_landing_concrete_01:parapet:") for value in ids)
    assert any(value.startswith("scene-platform:terrace_timber_01:deck:") for value in ids)
    assert any("scene-platform:terrace_timber_01:support" in value for value in ids)


def test_timber_platform_is_not_rendered_as_a_solid_masonry_block() -> None:
    model = augment_brick_model_with_scene_architecture(_base_model(), _scene(), front_width_studs=48)
    timber_deck = [part for part in model.parts if part.placement_id.startswith("scene-platform:terrace_timber_01:deck:")]
    assert timber_deck
    assert len({part.z_plates for part in timber_deck}) == 1
