from pathlib import Path


def test_scene_stage_wires_generator_directly():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert './scene-handoff-photo-evidence.js?v=scene-stage-bh146-standalone' in text
    assert './scene-stage-ui.js?v=scene-stage-ui-bh146-standalone' in text
