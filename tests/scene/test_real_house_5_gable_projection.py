import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.projection import project_scene_to_building


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_scene_real_house_5_v02.json"


def test_real_house_5_gable_survives_metric_scene_projection() -> None:
    scene = ArchitecturalScene.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    scene_roof = next(roof for roof in scene.roofs if roof.id == "main_gable_roof")
    assert scene_roof.type.value == "gable"
    assert scene_roof.ridge_direction.value == "depth"
    assert scene_roof.source.kind.value == "inferred"
    assert 10.0 < scene_roof.pitch_degrees < 30.0

    result = project_scene_to_building(scene)
    assert "gable_geometry_incomplete" not in {issue.code for issue in result.issues}
    assert result.building is not None

    roof = next(item for item in result.building.roofs if item.id == "main_gable_roof")
    assert roof.type.value == "gable"
    assert roof.ridge_direction.value == "depth"
    assert roof.pitch_degrees == scene_roof.pitch_degrees
