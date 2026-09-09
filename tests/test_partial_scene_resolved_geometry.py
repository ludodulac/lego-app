import json
from pathlib import Path

from brickhouse.partial_scene_pipeline import _partial_fidelity_issues, _resolved_core_building
from brickhouse.scene import ArchitecturalScene


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def _scene_payload() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_partial_preview_still_omits_incomplete_roof_without_guessing_geometry() -> None:
    scene = ArchitecturalScene.model_validate(_scene_payload())
    building = _resolved_core_building(scene)

    assert building.roofs == []
    assert any(
        issue.code == "partial_preview_roof_omitted" and issue.object_id == "roof_main"
        for issue in _partial_fidelity_issues(scene)
    )


def test_partial_preview_keeps_fully_specified_representable_roof() -> None:
    payload = _scene_payload()
    payload["roofs"][0].update(
        {
            "type": "gable",
            "ridge_direction": "depth",
            "down_slope_direction": None,
            "pitch_degrees": 20.0,
        }
    )
    scene = ArchitecturalScene.model_validate(payload)
    building = _resolved_core_building(scene)

    assert [roof.id for roof in building.roofs] == ["roof_main"]
    assert building.roofs[0].pitch_degrees == 20.0
    assert not any(
        issue.code == "partial_preview_roof_omitted" and issue.object_id == "roof_main"
        for issue in _partial_fidelity_issues(scene)
    )
