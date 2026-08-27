from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_shutters import augment_brick_model_with_scene_shutters
from brickhouse.scene import ArchitecturalScene


def _scene(*, state=None, style="folding", count=2, color="white") -> ArchitecturalScene:
    visual = {
        "shutter_count": count,
        "shutter_style": style,
        "shutter_color": color,
    }
    if state is not None:
        visual["shutter_state"] = state
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "shutter-scene",
        "name": "Shutter scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": .8}},
            "height": {"value": 5, "source": {"kind": "inferred", "confidence": .8}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .8},
        }],
        "openings": [{
            "id": "upper_window",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2,
            "offset_vertical": 2,
            "width": 2,
            "height": 2,
            "source": {"kind": "observed", "confidence": .95},
            "opening_visual": visual,
        }],
        "appearance": {},
    })


def _model() -> BrickModel:
    return BrickModel(
        building_id="shutter-scene",
        volume_id="main",
        width_studs=40,
        depth_studs=32,
        height_plates=60,
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


def _generated(scene):
    enriched = augment_brick_model_with_scene_shutters(_model(), scene, front_width_studs=40)
    return [part for part in enriched.parts if part.placement_id.startswith("scene-shutter:")]


def test_folding_style_without_observed_pose_does_not_invent_shutters():
    assert _generated(_scene(state=None)) == []


def test_free_text_open_pose_is_not_silently_normalized_into_geometry():
    assert _generated(_scene(state="open")) == []


def test_closed_pose_is_left_unrendered_until_an_outward_facade_plane_is_supported():
    assert _generated(_scene(state="closed_over_opening")) == []


def test_exact_open_folded_pose_generates_two_side_strips_outside_window_void():
    generated = _generated(_scene(state="open_folded_at_sides"))

    assert generated
    assert {part.opening_id for part in generated} == {"upper_window"}
    assert {part.part_id for part in generated} == {"BRICK_1X1"}
    assert {part.category for part in generated} == {"facade_detail"}
    columns = sorted({part.x_studs for part in generated})
    assert columns == [7, 16]
    # The 2 m opening raster spans x=8..15 at this 4 studs/m scale.
    assert all(part.x_studs not in range(8, 16) for part in generated)
    assert len({part.z_plates for part in generated if part.x_studs == 7}) > 1
    assert len({part.z_plates for part in generated if part.x_studs == 16}) > 1


def test_explicit_shutter_color_survives_as_semantic_color():
    generated = _generated(_scene(state="open_folded_at_sides", color="white"))
    assert generated
    assert {part.semantic_color for part in generated} == {"white"}


def test_wrong_count_or_nonfolding_style_does_not_generate_paired_folded_shutters():
    assert _generated(_scene(state="open_folded_at_sides", count=1)) == []
    assert _generated(_scene(state="open_folded_at_sides", style="roller")) == []
