from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.survey_validation import _local_grade_elevation


def test_local_grade_elevation_interpolates_at_opening_center():
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "grade-opening",
        "name": "Grade opening",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 10, "source": {"kind": "inferred", "confidence": .6}},
            "height": {"value": 6, "source": {"kind": "inferred", "confidence": .6}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .6},
        }],
        "openings": [{
            "id": "low_window",
            "type": "window",
            "volume_id": "main",
            "facade": "right",
            "offset_horizontal": 4.5,
            "offset_vertical": .75,
            "width": 1,
            "height": .75,
            "local_grade_clearance": 0,
            "source": {"kind": "inferred", "confidence": .7},
        }],
        "terrain": {"kind": "facade_grade_profiles", "profiles": [{
            "facade": "right",
            "start_elevation": 0,
            "end_elevation": 1.5,
            "source": {"kind": "inferred", "confidence": .6},
        }]},
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })
    assert abs(_local_grade_elevation(scene, scene.openings[0]) - .75) < 1e-9
