from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.7}


def _base_scene(platforms, stairs=None):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "edge-rendering",
        "name": "Edge rendering",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": platforms,
        "stairs": stairs or [],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def _span(part):
    return {
        "BRICK_1X1": 1,
        "BRICK_1X2": 2,
        "BRICK_1X3": 3,
        "BRICK_1X4": 4,
        "BRICK_1X6": 6,
        "BRICK_1X8": 8,
    }[part.part_id]


def _covered_axis_cells(part, axis):
    start = part.y_studs if axis == "y" else part.x_studs
    return set(range(start, start + _span(part)))


def test_platform_edges_are_rendered_independently_with_partial_access_gap():
    scene = _base_scene([{
        "id": "deck",
        "position": {"x": 10, "y": 2, "z": 1},
        "width": 2,
        "depth": 4,
        "thickness": 0.2,
        "material": "timber",
        "supports": [],
        "edges": {
            "x_min": {"treatment": "wall_attached"},
            "x_max": {"treatment": "open_railing", "access_spans": [{"from": 1.0, "to": 2.0}]},
            "y_min": {"treatment": "solid_parapet"},
            "y_max": {"treatment": "none"},
        },
        "source": SOURCE,
    }])
    bundle = run_m0_pipeline_scene(scene, front_width_studs=40)
    parts = bundle.brick_model.parts
    ids = [part.placement_id for part in parts]

    assert not any("scene-platform:deck:x_min:" in value for value in ids)
    assert any("scene-platform:deck:x_max:rail-top-solution:" in value for value in ids)
    assert any("scene-platform:deck:y_min:parapet:" in value for value in ids)
    assert not any("scene-platform:deck:y_max:" in value for value in ids)

    # 4 m edge at 4 studs/m = 16 cells. Access [1m,2m) removes cells 4..7.
    # The two remaining contiguous runs are exactly 4 and 8 studs, so they become
    # two approved structural bricks rather than twelve isolated 1x1 cells.
    rails = [part for part in parts if "scene-platform:deck:x_max:rail-top-solution:" in part.placement_id]
    assert len(rails) == 2
    assert sorted(part.part_id for part in rails) == ["BRICK_1X4", "BRICK_1X8"]
    assert all(part.rotation_quarter_turns == 0 for part in rails)
    relative_y = {cell - min(part.y_studs for part in rails) for part in rails for cell in _covered_axis_cells(part, "y")}
    assert relative_y == set(range(4)) | set(range(8, 16))


def test_open_railing_along_x_uses_rotated_long_bricks_without_changing_footprint():
    scene = _base_scene([{
        "id": "front-deck",
        "position": {"x": 2, "y": -2, "z": 1},
        "width": 4,
        "depth": 2,
        "thickness": 0.2,
        "material": "timber",
        "supports": [],
        "edges": {
            "x_min": {"treatment": "none"},
            "x_max": {"treatment": "none"},
            "y_min": {"treatment": "open_railing"},
            "y_max": {"treatment": "wall_attached"},
        },
        "source": SOURCE,
    }])
    bundle = run_m0_pipeline_scene(scene, front_width_studs=40)
    rails = [part for part in bundle.brick_model.parts if "scene-platform:front-deck:y_min:rail-top-solution:" in part.placement_id]

    # 4 m at 4 studs/m gives a continuous 16-stud rail: two 1x8 bricks, rotated
    # so their physical footprint follows X rather than Y.
    assert len(rails) == 2
    assert {part.part_id for part in rails} == {"BRICK_1X8"}
    assert all(part.rotation_quarter_turns == 1 for part in rails)
    covered = {cell for part in rails for cell in _covered_axis_cells(part, "x")}
    assert covered == set(range(min(covered), min(covered) + 16))


def test_stair_open_railing_and_solid_parapet_are_not_symmetric_defaults():
    scene = _base_scene(
        [{
            "id": "landing",
            "position": {"x": 10, "y": 2, "z": 1},
            "width": 2,
            "depth": 2,
            "thickness": 0.2,
            "material": "concrete",
            "supports": [],
            "edges": {"x_min": {"treatment": "wall_attached"}},
            "source": SOURCE,
        }],
        [{
            "id": "stair",
            "start": {"x": 12, "y": 3, "z": 0},
            "end": {"x": 11, "y": 3, "z": 1},
            "width": 1,
            "material": "concrete",
            "left_edge": "solid_parapet",
            "right_edge": "open_railing",
            "source": SOURCE,
        }],
    )
    bundle = run_m0_pipeline_scene(scene, front_width_studs=40)
    ids = [part.placement_id for part in bundle.brick_model.parts]
    assert any("scene-stair:stair:left-parapet:" in value for value in ids)
    assert any("scene-stair:stair:right-rail:" in value for value in ids)
    assert not any("scene-stair:stair:right-parapet:" in value for value in ids)
