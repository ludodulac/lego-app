from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.survey_validation import _stair_platform_access_holds


def _scene(access_from, access_to, stair_width=1.2):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "access-width",
        "name": "Access width",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": .6}},
            "height": {"value": 6, "source": {"kind": "inferred", "confidence": .6}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .6},
        }],
        "platforms": [{
            "id": "deck",
            "position": {"x": -2, "y": 2, "z": 2},
            "width": 2,
            "depth": 4,
            "thickness": .2,
            "material": "timber",
            "edges": {
                "x_min": {"treatment": "open_railing"},
                "x_max": {"treatment": "wall_attached"},
                "y_min": {"treatment": "open_railing", "access_spans": [{"from": access_from, "to": access_to}]},
                "y_max": {"treatment": "open_railing"},
            },
            "source": {"kind": "inferred", "confidence": .7},
        }],
        "stairs": [{
            "id": "stair",
            "start": {"x": -1, "y": 0, "z": 0},
            "end": {"x": -1, "y": 2, "z": 2},
            "width": stair_width,
            "material": "concrete",
            "source": {"kind": "inferred", "confidence": .7},
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_access_span_must_fit_whole_stair_width():
    scene = _scene(.7, 1.3, stair_width=1.2)
    assert not _stair_platform_access_holds(scene.stairs[0], scene.platforms[0])


def test_wide_access_span_accepts_whole_stair_width():
    scene = _scene(.3, 1.7, stair_width=1.2)
    assert _stair_platform_access_holds(scene.stairs[0], scene.platforms[0])
