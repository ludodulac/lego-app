from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.projection import project_scene_to_building
from brickhouse.geometry.generator import generate_building_geometry
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.windows import generate_window_assemblies


SOURCE = {"kind": "inferred", "confidence": 0.6}


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-unknown-opening",
            "name": "Generic unknown opening",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 10, "source": SOURCE},
                    "depth": {"value": 8, "source": SOURCE},
                    "height": {"value": 6, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                }
            ],
            "openings": [
                {
                    "id": "unknown-left-opening",
                    "type": "unknown",
                    "volume_id": "main",
                    "facade": "left",
                    "offset_horizontal": 3.0,
                    "offset_vertical": 1.2,
                    "width": 1.4,
                    "height": 1.5,
                    "source": SOURCE,
                    "evidence": [{"photo_index": 1, "observation": "physical opening visible, semantic type unknown"}],
                }
            ],
            "appearance": {},
        }
    )


def _primary_building():
    building = project_scene_to_building(_scene()).building
    assert building is not None
    return building


def test_unknown_opening_survives_projection_without_becoming_window_or_door() -> None:
    scene = _scene()
    opening = scene.openings[0]
    assert opening.type.value == "unknown"
    assert opening.window_style is None
    assert opening.has_sill is None
    assert opening.has_decorative_surround is None

    result = project_scene_to_building(scene)
    assert result.building is not None
    projected = result.building.openings[0]
    assert projected.id == "unknown-left-opening"
    assert projected.type.value == "unknown"


def test_unknown_opening_keeps_wall_void_but_is_not_fitted_as_window() -> None:
    building = _primary_building()
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, front_width_studs=48)

    left_wall = next(wall for wall in shell.walls if wall.facade.value == "left")
    assert any(item.id == "unknown-left-opening" for item in left_wall.grid.openings)

    _, fitted = generate_window_assemblies(building, shell)
    assert "unknown-left-opening" not in fitted
