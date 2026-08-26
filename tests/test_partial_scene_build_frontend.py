import json
import subprocess
from pathlib import Path

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene, project_scene_to_building


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "brickhouse_scene_current.json"


def _prepare_with_frontend_policy() -> dict:
    script = """
import fs from 'node:fs';
import { prepareConservativePartialScene } from './frontend/partial-scene-build.js';
const scene = JSON.parse(fs.readFileSync('./tests/fixtures/brickhouse_scene_current.json', 'utf8'));
process.stdout.write(JSON.stringify(prepareConservativePartialScene(scene)));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_current_house_can_build_trustworthy_known_bricks_before_roof_is_resolved() -> None:
    prepared = _prepare_with_frontend_policy()
    omitted = {item["object_id"]: item["reason"] for item in prepared["omitted"]}

    assert omitted == {
        "roof_main": "toiture non résolue",
        "timber_deck": "raccord métrique non résolu",
        "exterior_stair": "raccord métrique non résolu",
    }

    partial = ArchitecturalScene.model_validate(prepared["scene"])
    assert partial.roofs == []
    assert partial.platforms == []
    assert partial.stairs == []
    assert {volume.id for volume in partial.volumes} == {
        "volume_main",
        "lower_exterior_volume",
    }
    assert len(partial.openings) == 11

    projection = project_scene_to_building(partial)
    assert projection.building is not None
    assert not projection.blocked

    bundle = run_m0_pipeline_scene(partial, front_width_studs=48)
    placement_ids = {part.placement_id for part in bundle.brick_model.parts}

    assert bundle.brick_model.parts
    assert any(part.component == "wall" for part in bundle.brick_model.parts)
    assert any(part.category in {"window_frame", "window_pane"} for part in bundle.brick_model.parts)
    assert not any(part.component == "roof" for part in bundle.brick_model.parts)
    assert not any(value.startswith("scene-platform:") for value in placement_ids)
    assert not any(value.startswith("scene-stair:") for value in placement_ids)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_steps > 0
    assert bundle.assembly_plan.steps[0].sequence == 1


def test_partial_policy_does_not_mutate_authoritative_scene() -> None:
    original = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prepared = _prepare_with_frontend_policy()

    assert len(original["roofs"]) == 1
    assert len(original["platforms"]) == 1
    assert len(original["stairs"]) == 1
    assert prepared["scene"] is not original
