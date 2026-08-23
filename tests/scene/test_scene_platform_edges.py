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
    ids = [part.placement_id for part in bundle.brick_model.parts]

    assert not any("scene-platform:deck:x_min:" in value for value in ids)
    assert any("scene-platform:deck:x_max:rail-top:" in value for value in ids)
    assert any("scene-platform:deck:y_min:parapet:" in value for value in ids)
    assert not any("scene-platform:deck:y_max:" in value for value in ids)

    # 4 m edge at 4 studs/m = 16 cells. A 1 m wide access removes four top-rail cells.
    x_max_top = [value for value in ids if "scene-platform:deck:x_max:rail-top:" in value]
    assert len(x_max_top) == 12


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
