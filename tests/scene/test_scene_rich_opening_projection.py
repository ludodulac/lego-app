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
            "opening_visual": {
                "frame_color": "dark_brown",
                "frame_material": "wood",
                "leaf_count": 2,
                "pane_count": 4,
                "mullion_count": 1,
                "glazing": "clear",
                "sill": "projecting",
                "surround_material": "stone_like",
                "surround_color": "light_beige",
                "shutter_count": 2,
                "shutter_style": "folding",
                "shutter_color": "white",
            },
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
    assert opening.opening_visual is not None
    assert opening.opening_visual.leaf_count == 2
    assert opening.opening_visual.pane_count == 4
    assert opening.opening_visual.mullion_count == 1
    assert opening.opening_visual.surround_material == "stone_like"
    assert opening.opening_visual.shutter_count == 2
    assert opening.opening_visual.shutter_style == "folding"
    assert opening.opening_visual.shutter_color == "white"


def test_door_composition_survives_without_window_only_metadata():
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "rich-door",
        "name": "Rich door",
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
            "id": "door_01",
            "type": "door",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 6,
            "offset_vertical": 0,
            "width": 1.8,
            "height": 2.2,
            "opening_visual": {
                "frame_color": "dark_brown",
                "leaf_count": 2,
                "pane_count": 4,
                "mullion_count": 1,
                "glazing": "clear",
            },
            "source": {"kind": "observed", "confidence": .95},
        }],
        "appearance": {"walls": {"color": "off_white"}},
    })
    result = project_scene_to_building(scene)
    assert not result.blocked
    opening = result.building.openings[0]
    assert opening.type.value == "door"
    assert opening.opening_visual.leaf_count == 2
    assert opening.opening_visual.pane_count == 4
    assert opening.opening_visual.glazing == "clear"
    assert opening.window_style is None
