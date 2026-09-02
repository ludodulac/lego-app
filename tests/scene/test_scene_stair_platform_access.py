import pytest

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.7}


def _scene(access_spans, *, treatment="open_railing", stair_width=1.0):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "stair-platform-access",
        "name": "Stair platform access",
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
        "platforms": [{
            "id": "landing",
            "position": {"x": 10, "y": 2, "z": 1},
            "width": 2,
            "depth": 4,
            "thickness": 0.2,
            "material": "timber",
            "supports": [],
            "edges": {
                "x_min": {"treatment": "wall_attached"},
                "x_max": {"treatment": treatment, "access_spans": access_spans},
                "y_min": {"treatment": "none"},
                "y_max": {"treatment": "none"},
            },
            "source": SOURCE,
        }],
        "stairs": [{
            "id": "garden-stair",
            "start": {"x": 14, "y": 4, "z": 0},
            "end": {"x": 12, "y": 4, "z": 1},
            "width": stair_width,
            "material": "timber",
            "left_edge": "open_railing",
            "right_edge": "open_railing",
            "source": SOURCE,
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def test_guarded_platform_edge_accepts_stair_when_access_covers_full_width():
    scene = _scene([{"from": 1.5, "to": 2.5}])
    bundle = run_m0_pipeline_scene(scene, front_width_studs=40)

    ids = [part.placement_id for part in bundle.brick_model.parts]
    assert any(value.startswith("scene-stair:garden-stair:tread:") for value in ids)
    rails = [
        part for part in bundle.brick_model.parts
        if "scene-platform:landing:x_max:rail-top-solution:" in part.placement_id
    ]
    assert rails
    # The declared access remains empty; stair geometry is not used to invent or
    # widen a platform opening after the fact.
    covered_y = set()
    span_by_id = {
        "BRICK_1X1": 1, "BRICK_1X2": 2, "BRICK_1X3": 3,
        "BRICK_1X4": 4, "BRICK_1X6": 6, "BRICK_1X8": 8,
    }
    for part in rails:
        covered_y.update(range(part.y_studs, part.y_studs + span_by_id[part.part_id]))
    stair_end_y = round(4 * 4)
    assert stair_end_y not in covered_y


def test_guarded_platform_edge_rejects_stair_without_declared_access():
    scene = _scene([])
    with pytest.raises(ValueError, match="without an access span covering the stair width"):
        run_m0_pipeline_scene(scene, front_width_studs=40)


def test_guarded_platform_edge_rejects_access_narrower_than_stair():
    scene = _scene([{"from": 1.75, "to": 2.25}], stair_width=1.0)
    with pytest.raises(ValueError, match="without an access span covering the stair width"):
        run_m0_pipeline_scene(scene, front_width_studs=40)


def test_explicit_whole_edge_access_does_not_require_spans():
    scene = _scene([], treatment="access_opening")
    bundle = run_m0_pipeline_scene(scene, front_width_studs=40)
    assert any(
        part.placement_id.startswith("scene-stair:garden-stair:tread:")
        for part in bundle.brick_model.parts
    )
