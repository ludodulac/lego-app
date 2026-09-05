from pathlib import Path


def test_scene_stage_has_exactly_one_user_action():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert text.count('class="primary big-action"') == 1
    assert text.count('id="download-scene-handoff"') == 1
