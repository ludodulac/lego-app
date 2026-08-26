from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.wall_depth import augment_brick_model_with_wall_depth
from brickhouse.scene import ArchitecturalScene


def _source():
    return {"kind": "user_provided", "confidence": 1.0}


def _scene():
    volume = lambda volume_id, x: {
        "id": volume_id,
        "position": {"x": x, "y": 0, "z": 0},
        "width": {"value": 10.0, "source": _source(), "evidence": []},
        "depth": {"value": 8.0, "source": _source(), "evidence": []},
        "height": {"value": 3.0, "source": _source(), "evidence": []},
        "floors": 1,
        "source": _source(),
        "evidence": [],
    }
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "composite-depth-house",
        "name": "Composite depth house",
        "units": "m",
        "volumes": [volume("main", 0), volume("wing", 12)],
        "openings": [],
        "roofs": [],
        "appearance": {},
        "wall_profile_observations": [{
            "id": "wing-front-depth",
            "volume_id": "wing",
            "facade": "front",
            "openings_recessed": True,
            "wall_thickness": {"value": 1.0, "source": _source(), "evidence": []},
            "reveal_depth": {"value": 0.5, "source": _source(), "evidence": []},
            "source": _source(),
            "evidence": [],
        }],
    })


def _wall(placement_id, x):
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X2",
        category="brick",
        component="wall",
        x_studs=x,
        y_studs=0,
        z_plates=0,
        rotation_quarter_turns=1,
        facade="front",
    )


def _frame(placement_id, x):
    return BrickModelPart(
        placement_id=placement_id,
        part_id="WINDOW_1X2X2_60592",
        category="window_frame",
        component="facade_detail",
        x_studs=x,
        y_studs=0,
        z_plates=0,
        rotation_quarter_turns=1,
        facade="front",
    )


def test_composite_wall_depth_respects_volume_prefixes():
    model = BrickModel(
        building_id="composite-depth-house",
        volume_id="composite",
        width_studs=44,
        depth_studs=16,
        height_plates=9,
        parts=[
            _wall("main:wall-000001", 0),
            _frame("main:window-000001", 2),
            _wall("wing:wall-000001", 24),
            _frame("wing:window-000001", 26),
        ],
    )

    result = augment_brick_model_with_wall_depth(model, _scene(), front_width_studs=20)

    main_frame = next(part for part in result.parts if part.placement_id == "main:window-000001")
    wing_frame = next(part for part in result.parts if part.placement_id == "wing:window-000001")
    assert main_frame.y_studs == 0
    assert wing_frame.y_studs == 1

    depth_parts = [part for part in result.parts if part.placement_id.startswith("wall-depth:wing-front-depth:")]
    assert len(depth_parts) == 1
    assert depth_parts[0].x_studs == 24
    assert depth_parts[0].y_studs == 1
    assert not any(part.placement_id.startswith("wall-depth:wing-front-depth:") and part.x_studs == 0 for part in result.parts)
