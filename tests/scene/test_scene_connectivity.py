import pytest
from pydantic import ValidationError

from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _scene(*, platform=None, stairs=None, openings=None):
    return {
        "schema_version": "0.2",
        "id": "connectivity",
        "name": "Connectivity",
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
        "openings": openings or [],
        "platforms": [platform] if platform else [],
        "stairs": stairs or [],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    }


def _platform(x=10, y=2, z=1, id="deck"):
    return {"id": id, "position": {"x": x, "y": y, "z": z}, "width": 2, "depth": 3, "thickness": 0.2, "source": SOURCE}


def _stair(start, end, id="stair"):
    return {"id": id, "start": start, "end": end, "width": 1, "source": SOURCE}


def _door(facade="right", offset=3, z=1, id="door"):
    return {
        "id": id,
        "type": "door",
        "volume_id": "main",
        "facade": facade,
        "offset_horizontal": offset,
        "offset_vertical": z,
        "width": 1,
        "height": 2,
        "source": SOURCE,
    }


def test_accepts_ground_to_platform_stair_when_platform_touches_building():
    scene = _scene(
        platform=_platform(),
        stairs=[_stair({"x": 12, "y": 3, "z": 0}, {"x": 11, "y": 3, "z": 1})],
    )
    assert ArchitecturalScene.model_validate(scene).platforms[0].id == "deck"


def test_rejects_floating_stair_endpoint():
    scene = _scene(
        platform=_platform(),
        stairs=[_stair({"x": 12, "y": 3, "z": 0}, {"x": 14, "y": 3, "z": 1})],
    )
    with pytest.raises(ValidationError, match="does not connect to ground, a platform, or the building"):
        ArchitecturalScene.model_validate(scene)


def test_rejects_isolated_platform():
    scene = _scene(platform=_platform(x=15, y=15, z=1))
    with pytest.raises(ValidationError, match="disconnected from both building and stairs"):
        ArchitecturalScene.model_validate(scene)


def test_accepts_two_stair_runs_joined_by_platform():
    landing = _platform(x=10, y=2, z=1)
    scene = _scene(
        platform=landing,
        stairs=[
            _stair({"x": 12, "y": 3, "z": 0}, {"x": 11.5, "y": 3, "z": 1}, "lower"),
            _stair({"x": 10.5, "y": 3, "z": 1}, {"x": 10, "y": 3, "z": 2}, "upper"),
        ],
    )
    assert len(ArchitecturalScene.model_validate(scene).stairs) == 2


def test_elevated_door_without_access_is_valid_without_explicit_relationship():
    # Real buildings can have loading doors, removed balconies, future access,
    # or intentionally inaccessible openings. Access must only be enforced when
    # the Survey explicitly establishes that relationship.
    scene = _scene(openings=[_door(facade="right", offset=3, z=2)])
    assert ArchitecturalScene.model_validate(scene).openings[0].id == "door"
