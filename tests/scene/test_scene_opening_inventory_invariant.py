from brickhouse.scene import ArchitecturalScene, project_scene_to_building


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "opening-inventory",
        "name": "Generic opening inventory",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 12, "source": SOURCE},
            "depth": {"value": 9, "source": SOURCE},
            "height": {"value": 8, "source": SOURCE},
            "floors": 3,
            "source": SOURCE,
        }],
        "openings": [
            {"id": "front-a", "type": "window", "volume_id": "main", "facade": "front", "offset_horizontal": 1.2, "offset_vertical": 1.5, "width": 1.4, "height": 1.8, "source": SOURCE},
            {"id": "front-b", "type": "door", "volume_id": "main", "facade": "front", "offset_horizontal": 7.4, "offset_vertical": 0, "width": 1.1, "height": 2.2, "source": SOURCE},
            {"id": "left-a", "type": "window", "volume_id": "main", "facade": "left", "offset_horizontal": 2.0, "offset_vertical": 4.3, "width": 1.0, "height": 1.4, "source": SOURCE},
            {"id": "right-a", "type": "window", "volume_id": "main", "facade": "right", "offset_horizontal": 6.1, "offset_vertical": 0.7, "width": 1.6, "height": 1.0, "source": SOURCE},
        ],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_projection_preserves_exact_opening_inventory_facades_and_metric_geometry():
    scene = _scene()
    result = project_scene_to_building(scene)
    assert result.blocked is False
    assert result.building is not None

    before = {
        opening.id: (
            opening.type.value,
            opening.facade.value,
            opening.offset_horizontal,
            opening.offset_vertical,
            opening.width,
            opening.height,
        )
        for opening in scene.openings
    }
    after = {
        opening.id: (
            opening.type.value,
            opening.facade.value,
            opening.offset_horizontal,
            opening.offset_vertical,
            opening.width,
            opening.height,
        )
        for opening in result.building.openings
    }
    assert after == before


def test_projection_does_not_create_openings_on_empty_facade():
    result = project_scene_to_building(_scene())
    assert result.building is not None
    assert not any(opening.facade.value == "rear" for opening in result.building.openings)
