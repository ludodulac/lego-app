from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.wall_depth import augment_brick_model_with_wall_depth
from brickhouse.scene import ArchitecturalScene


def _source(kind="user_provided", confidence=1.0):
    return {"kind": kind, "confidence": confidence}


def _scene(*, thickness=1.0, reveal=0.5, confidence=1.0):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "depth-house",
        "name": "Depth house",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10.0, "source": _source(), "evidence": []},
            "depth": {"value": 8.0, "source": _source(), "evidence": []},
            "height": {"value": 3.0, "source": _source(), "evidence": []},
            "floors": 1,
            "source": _source(),
            "evidence": [],
        }],
        "openings": [],
        "roofs": [],
        "appearance": {},
        "wall_profile_observations": [{
            "id": "front-depth",
            "volume_id": "main",
            "facade": "front",
            "openings_recessed": True,
            "wall_thickness": {
                "value": thickness,
                "source": _source("inferred", confidence),
                "evidence": [],
            } if thickness is not None else None,
            "reveal_depth": {
                "value": reveal,
                "source": _source("inferred", confidence),
                "evidence": [],
            } if reveal is not None else None,
            "source": _source("inferred", confidence),
            "evidence": [],
        }],
    })


def _model():
    return BrickModel(
        building_id="depth-house",
        volume_id="main",
        width_studs=20,
        depth_studs=16,
        height_plates=9,
        parts=[
            BrickModelPart(
                placement_id="wall-left",
                part_id="BRICK_1X2",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="wall-right",
                part_id="BRICK_1X2",
                category="brick",
                component="wall",
                x_studs=4,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="window-frame",
                part_id="WINDOW_1X2X2_60592",
                category="window_frame",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="window-pane",
                part_id="GLASS_FOR_WINDOW_1X2X2_60601",
                category="window_pane",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
                facade="front",
            ),
        ],
    )


def test_resolved_wall_depth_adds_inner_masonry_and_recesses_window():
    result = augment_brick_model_with_wall_depth(_model(), _scene(), front_width_studs=20)

    added = [part for part in result.parts if part.placement_id.startswith("wall-depth:")]
    assert len(added) == 2
    assert {part.y_studs for part in added} == {1}
    assert not any(part.x_studs == 2 and part.y_studs == 1 and part.component == "wall" for part in result.parts)

    frame = next(part for part in result.parts if part.placement_id == "window-frame")
    pane = next(part for part in result.parts if part.placement_id == "window-pane")
    assert frame.y_studs == 1
    assert pane.y_studs == 1


def test_low_confidence_or_unknown_depth_never_guesses_geometry():
    low_confidence = augment_brick_model_with_wall_depth(
        _model(), _scene(confidence=0.4), front_width_studs=20
    )
    assert low_confidence == _model()

    unknown = augment_brick_model_with_wall_depth(
        _model(), _scene(thickness=None, reveal=None, confidence=0.9), front_width_studs=20
    )
    assert unknown == _model()
