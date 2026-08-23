from brickhouse.scene import ArchitecturalScene, project_scene_to_building


def test_window_metadata_survives_scene_projection():
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "rich-window",
        "name": "Rich window",
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
        "openings": [{
            "id": "window_01",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2,
            "offset_vertical": 2,
            "width": 1.4,
            "height": 1.5,
            "window_style": "traditional_tall",
            "has_sill": True,
            "has_decorative_surround": True,
            "source": {"kind": "inferred", "confidence": .7},
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })
    result = project_scene_to_building(scene)
    assert not result.blocked
    opening = result.building.openings[0]
    assert opening.window_style.value == "traditional_tall"
    assert opening.has_sill is True
    assert opening.has_decorative_surround is True
