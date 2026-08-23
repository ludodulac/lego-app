from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


def _base_model() -> BrickModel:
    return BrickModel(
        building_id="generic-building",
        volume_id="main",
        width_studs=48,
        depth_studs=48,
        height_plates=60,
        parts=[
            BrickModelPart(
                placement_id="wall-seed",
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


def _scene(*, reverse: bool = False) -> ArchitecturalScene:
    start = {"x": -2.0, "y": 4.0, "z": 0.0}
    end = {"x": 0.0, "y": 4.0, "z": 1.2}
    if reverse:
        start, end = end, start
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "stair-centerline",
            "name": "Generic centered stair",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 10, "source": {"kind": "inferred", "confidence": 0.7}},
                    "depth": {"value": 10, "source": {"kind": "inferred", "confidence": 0.7}},
                    "height": {"value": 6, "source": {"kind": "inferred", "confidence": 0.7}},
                    "floors": 2,
                    "source": {"kind": "inferred", "confidence": 0.7},
                }
            ],
            "stairs": [
                {
                    "id": "stair",
                    "start": start,
                    "end": end,
                    "width": 1.0,
                    "material": "concrete",
                    "left_edge": "solid_parapet",
                    "right_edge": "solid_parapet",
                    "source": {"kind": "inferred", "confidence": 0.7},
                }
            ],
            "appearance": {"walls": {"color": "white"}, "roof": {"color": "gray"}},
        }
    )


def _stair_parts(reverse: bool = False):
    model = augment_brick_model_with_scene_architecture(
        _base_model(), _scene(reverse=reverse), front_width_studs=48
    )
    return [part for part in model.parts if part.placement_id.startswith("scene-stair:stair:")]


def test_stair_width_is_centered_on_scene_run_axis() -> None:
    parts = _stair_parts()
    treads = [part for part in parts if ":tread:" in part.placement_id]
    assert treads
    by_x = {}
    for part in treads:
        by_x.setdefault(part.x_studs, set()).add(part.y_studs)
    widest = max(by_x.values(), key=len)
    center = (min(widest) + max(widest)) / 2
    # A 1m stair at 4.8 studs/m quantizes to five studs and should straddle,
    # not start at, its centerline.
    assert len(widest) == 5
    assert min(widest) < center < max(widest)


def test_left_and_right_parapets_follow_travel_direction() -> None:
    forward = _stair_parts(False)
    reverse = _stair_parts(True)

    forward_left = [part.y_studs for part in forward if ":left-parapet:" in part.placement_id]
    forward_right = [part.y_studs for part in forward if ":right-parapet:" in part.placement_id]
    reverse_left = [part.y_studs for part in reverse if ":left-parapet:" in part.placement_id]
    reverse_right = [part.y_studs for part in reverse if ":right-parapet:" in part.placement_id]

    assert forward_left and forward_right and reverse_left and reverse_right
    # Moving +x: physical left is +y. Reversing the run swaps the world sides.
    assert min(forward_left) > max(forward_right)
    assert max(reverse_left) < min(reverse_right)
