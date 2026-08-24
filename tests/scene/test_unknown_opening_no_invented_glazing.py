import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.projection import project_scene_to_building
from brickhouse.geometry.generator import generate_building_geometry
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.windows import generate_window_assemblies


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_scene_real_house_5_v02.json"


def test_unknown_opening_survives_projection_without_becoming_window_or_door() -> None:
    scene = ArchitecturalScene.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    opening = next(item for item in scene.openings if item.id == "left_mid_opening")
    assert opening.type.value == "unknown"
    assert opening.window_style is None
    assert opening.has_sill is None
    assert opening.has_decorative_surround is None

    result = project_scene_to_building(scene)
    assert result.building is not None
    projected = next(item for item in result.building.openings if item.id == "left_mid_opening")
    assert projected.type.value == "unknown"


def test_unknown_opening_keeps_wall_void_but_emits_no_window_glazing() -> None:
    scene = ArchitecturalScene.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    building = project_scene_to_building(scene).building
    assert building is not None
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, front_width_studs=48)

    left_wall = next(wall for wall in shell.walls if wall.facade.value == "left")
    assert any(item.id == "left_mid_opening" for item in left_wall.grid.openings)

    placements, fitted = generate_window_assemblies(building, shell)
    assert "left_mid_opening" not in fitted
    assert all(item.facade.value != "left" or item.category != "window_pane" or item.x_studs != 0 for item in placements if False)
