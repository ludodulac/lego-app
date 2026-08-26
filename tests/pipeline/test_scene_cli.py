import json
from pathlib import Path

from brickhouse.scene_cli import main, write_scene_export


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_scene_cli_builds_current_five_photo_scene_into_lego(tmp_path: Path) -> None:
    output = tmp_path / "brickhouse-scene-export.json"

    bundle = write_scene_export(FIXTURE, output, front_width_studs=48)

    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["brick_model"]["building_id"] == bundle.brick_model.building_id
    placement_ids = {part.placement_id for part in bundle.brick_model.parts}
    assert any(value.startswith("scene-platform:timber_deck:") for value in placement_ids)
    assert any(value.startswith("scene-stair:exterior_stair:") for value in placement_ids)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_steps > 0


def test_scene_cli_main_writes_export(tmp_path: Path) -> None:
    output = tmp_path / "scene.json"
    assert main([str(FIXTURE), str(output), "--front-width-studs", "48"]) == 0
    assert output.exists()
