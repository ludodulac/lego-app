import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene, project_scene_to_building


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_scene_real_house_5_v02.json"


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_real_house_5_scene_parses_with_exact_backend_contract():
    scene = _scene()
    assert scene.schema_version == "0.2"
    assert scene.volumes[0].width.value == 10.0
    assert len(scene.openings) == 10
    assert scene.roofs[0].id == "main_gable_roof"
    assert scene.roofs[0].type.value == "gable"
    assert scene.roofs[0].ridge_direction.value == "depth"
    assert scene.roofs[0].pitch_degrees is None


def test_real_house_5_platform_supports_are_support_posts_not_strings():
    scene = _scene()
    terrace = next(item for item in scene.platforms if item.id == "left_timber_terrace")
    assert len(terrace.supports) == 2
    assert {post.id for post in terrace.supports} == {
        "left_timber_terrace_post_front",
        "left_timber_terrace_post_rear",
    }
    assert all(post.width > 0 and post.depth > 0 and post.height > 0 for post in terrace.supports)


def test_real_house_5_projection_is_blocked_only_after_scene_validation_by_unresolved_topology():
    scene = _scene()
    result = project_scene_to_building(scene)
    blocker_codes = {issue.code for issue in result.issues if issue.severity.value == "blocker"}
    assert "topological_relation_geometry_unresolved" in blocker_codes
    assert result.building is None
