from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_glazing import (
    FOUR_PANE_TALL_OVER_SQUARER,
    augment_brick_model_with_scene_glazing,
)
from brickhouse.scene import ArchitecturalScene


def _scene(
    *,
    evidence: str,
    glazing=None,
    width: float = 1.2,
    height: float = 2,
    leaf_count: int | None = None,
    pane_count: int | None = None,
    pane_layout: str | None = None,
) -> ArchitecturalScene:
    opening = {
        "id": "service_door",
        "type": "door",
        "volume_id": "main",
        "facade": "left",
        "offset_horizontal": 2,
        "offset_vertical": 0,
        "width": width,
        "height": height,
        "source": {"kind": "inferred", "confidence": .7},
        "evidence": [{"photo_index": 1, "observation": evidence}],
    }
    visual = {}
    if glazing is not None:
        visual["glazing"] = glazing
    if leaf_count is not None:
        visual["leaf_count"] = leaf_count
    if pane_count is not None:
        visual["pane_count"] = pane_count
    if pane_layout is not None:
        visual["pane_layout"] = pane_layout
    if visual:
        opening["opening_visual"] = visual
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "door-scene",
        "name": "Door scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": .7}},
            "height": {"value": 5, "source": {"kind": "inferred", "confidence": .7}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .7},
        }],
        "openings": [opening],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def _model() -> BrickModel:
    return BrickModel(
        building_id="door-scene",
        volume_id="main",
        width_studs=48,
        depth_studs=38,
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


def _generated(scene: ArchitecturalScene):
    enriched = augment_brick_model_with_scene_glazing(_model(), scene, front_width_studs=48)
    return [
        part
        for part in enriched.parts
        if part.placement_id.startswith("scene-glazing:service_door:")
    ]


def test_explicit_non_glazed_door_is_not_filled_with_scene_glazing():
    assert not _generated(_scene(evidence="Grande ouverture non vitrée d’accès."))


def test_structured_glazing_generates_door_panes_without_text_keyword():
    generated = _generated(_scene(evidence="Porte d’accès principale.", glazing="clear"))
    assert generated
    assert {part.category for part in generated} == {"window_pane"}
    assert {part.opening_id for part in generated} == {"service_door"}


def test_structured_negative_glazing_overrides_misleading_legacy_text():
    assert not _generated(_scene(evidence="Ancienne note: glazed door.", glazing="unglazed"))


def test_structured_unknown_glazing_does_not_invent_geometry_from_legacy_text():
    assert not _generated(_scene(evidence="Possibly glazed door.", glazing="unknown"))


def test_absent_structured_glazing_preserves_legacy_text_fallback():
    generated = _generated(_scene(evidence="Large glazed door visible."))
    assert generated
    assert {part.opening_id for part in generated} == {"service_door"}


def test_two_leaf_door_gets_exact_centerline_when_raster_width_is_odd():
    generated = _generated(
        _scene(
            evidence="Porte vitrée à deux vantaux.",
            glazing="clear",
            width=1.0,
            leaf_count=2,
        )
    )
    frames = [part for part in generated if part.category == "window_frame"]
    panes = [part for part in generated if part.category == "window_pane"]

    assert frames
    assert panes
    assert {part.opening_id for part in generated} == {"service_door"}
    assert len({part.y_studs for part in frames}) == 1
    frame_y = frames[0].y_studs
    pane_columns = {part.y_studs for part in panes}
    assert len([y for y in pane_columns if y < frame_y]) == 2
    assert len([y for y in pane_columns if y > frame_y]) == 2


def test_two_leaf_door_stays_fully_glazed_when_center_falls_between_studs():
    generated = _generated(
        _scene(
            evidence="Porte vitrée à deux vantaux.",
            glazing="clear",
            width=1.2,
            leaf_count=2,
        )
    )
    assert generated
    assert {part.category for part in generated} == {"window_pane"}


def test_pane_count_does_not_invent_horizontal_or_vertical_dividers():
    generated = _generated(
        _scene(
            evidence="Porte vitrée avec quatre panneaux visibles.",
            glazing="clear",
            width=1.0,
            pane_count=4,
        )
    )
    assert generated
    assert {part.category for part in generated} == {"window_pane"}


def test_reference_like_four_pane_layout_gets_shape_constrained_cross() -> None:
    generated = _generated(
        _scene(
            evidence="Deux vantaux, deux vitrages hauts rectangulaires et deux bas plus carrés.",
            glazing="clear",
            width=1.9,
            height=2.25,
            leaf_count=2,
            pane_count=4,
            pane_layout=FOUR_PANE_TALL_OVER_SQUARER,
        )
    )
    frames = [part for part in generated if part.category == "window_frame"]
    panes = [part for part in generated if part.category == "window_pane"]

    # 1.9 m at 48 studs / 10 m -> 9 stud columns. 2.25 m -> 9 courses.
    assert len(generated) == 81
    assert len(frames) == 17  # 9-cell center stile + 9-cell cross rail - intersection
    assert len(panes) == 64

    frame_columns = {}
    for part in frames:
        frame_columns.setdefault(part.y_studs, set()).add(part.z_plates)
    center_y = max(frame_columns, key=lambda y: len(frame_columns[y]))
    assert len(frame_columns[center_y]) == 9

    frame_rows = {}
    for part in frames:
        frame_rows.setdefault(part.z_plates, set()).add(part.y_studs)
    divider_z = max(frame_rows, key=lambda z: len(frame_rows[z]))
    assert len(frame_rows[divider_z]) == 9

    lower_rows = {part.z_plates for part in panes if part.z_plates < divider_z}
    upper_rows = {part.z_plates for part in panes if part.z_plates > divider_z}
    assert len(lower_rows) == 3
    assert len(upper_rows) == 5


def test_four_pane_layout_stays_without_cross_rail_when_shape_constraints_fail() -> None:
    generated = _generated(
        _scene(
            evidence="Deux vantaux et quatre vitrages, proportions non résolues à cette échelle.",
            glazing="clear",
            width=1.0,
            height=1.2,
            leaf_count=2,
            pane_count=4,
            pane_layout=FOUR_PANE_TALL_OVER_SQUARER,
        )
    )
    frames = [part for part in generated if part.category == "window_frame"]

    # The exact vertical leaf meeting line remains valid, but the shallow opening
    # cannot satisfy lower-near-square + distinctly-taller-upper constraints.
    assert frames
    assert len({part.y_studs for part in frames}) == 1
