import json
from pathlib import Path

import pytest

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene, project_scene_to_building
from brickhouse.survey import Certainty


FIXTURES = Path(__file__).parents[1] / "fixtures"
OLD_SCENE = FIXTURES / "architectural_scene_real_house_5_v02.json"
CURRENT_SCENE = FIXTURES / "architectural_scene_real_house_5_v25.json"


def _load(path: Path) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_certain_unresolved_relation_still_blocks_projection() -> None:
    scene = _load(OLD_SCENE)

    result = project_scene_to_building(scene)

    blockers = [
        issue
        for issue in result.issues
        if issue.code == "topological_relation_geometry_unresolved"
        and issue.severity.value == "blocker"
    ]
    assert blockers
    assert result.building is None
    assert all(
        next(relation for relation in scene.relations if relation.id == issue.object_id).certainty
        is Certainty.CERTAIN
        for issue in blockers
    )


def test_full_pipeline_cannot_bypass_certain_unresolved_relation() -> None:
    scene = _load(OLD_SCENE)

    with pytest.raises(ValueError, match="raccord métrique"):
        run_m0_pipeline_scene(scene, front_width_studs=48)


def test_plausible_unresolved_relation_is_preserved_without_blocking_m0() -> None:
    scene = _load(CURRENT_SCENE)
    relation = next(
        relation
        for relation in scene.relations
        if relation.id == "rel_lower_structure_landing"
    )
    before = relation.model_dump(mode="json")

    result = project_scene_to_building(scene)

    issue = next(
        issue
        for issue in result.issues
        if issue.object_id == "rel_lower_structure_landing"
        and issue.code == "topological_relation_geometry_unresolved"
    )
    assert issue.severity.value == "warning"
    assert result.building is not None
    assert not result.blocked
    assert relation.certainty is Certainty.PLAUSIBLE
    assert relation.geometry_status == "unresolved"
    assert relation.model_dump(mode="json") == before
    assert any(item.id == relation.id for item in scene.relations)


def test_current_real_house_5_benchmark_reaches_corrected_m0_projection() -> None:
    scene = _load(CURRENT_SCENE)

    projection = project_scene_to_building(scene)

    assert projection.building is not None
    assert not projection.blocked
    assert len(projection.building.volumes) == 2
    assert len(projection.building.openings) == 10
    assert {opening.id for opening in projection.building.openings} == {
        opening.id for opening in scene.openings
    }
    issues = {(issue.code, issue.object_id, issue.severity.value) for issue in projection.issues}
    assert (
        "topological_relation_geometry_unresolved",
        "rel_lower_structure_landing",
        "warning",
    ) in issues
    assert ("terrain_geometry_incomplete", "terrain:right", "warning") in issues
    assert ("roof_type_not_supported", "main_gable_roof", "warning") in issues


def test_current_real_house_5_benchmark_reaches_lego_without_inventing_unknown_grade() -> None:
    scene = _load(CURRENT_SCENE)
    profile = scene.terrain.profiles[0]
    assert profile.start_elevation == 0.0
    assert profile.end_elevation is None

    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)
    ids = [part.placement_id for part in bundle.brick_model.parts]

    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.bom.total_parts > 0
    assert any(value.startswith("scene-platform:left_timber_terrace:board:") for value in ids)
    assert any(value.startswith("scene-platform:left_concrete_landing:deck:") for value in ids)
    assert any(value.startswith("scene-stair:left_exterior_stair:tread:") for value in ids)
    assert not any(value.startswith("scene-terrain:right:") for value in ids)
    assert profile.end_elevation is None

    fidelity = {(issue.code, issue.object_id, issue.severity) for issue in bundle.fidelity_issues}
    assert (
        "topological_relation_geometry_unresolved",
        "rel_lower_structure_landing",
        "warning",
    ) in fidelity
    assert ("terrain_geometry_incomplete", "terrain:right", "warning") in fidelity
    assert ("roof_type_not_supported", "main_gable_roof", "warning") in fidelity
    assert ("chimney_not_supported", "chimney_front_left", "warning") in fidelity
    assert ("chimney_not_supported", "chimney_rear_area", "warning") in fidelity
