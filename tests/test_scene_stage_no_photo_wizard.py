from pathlib import Path


def test_scene_stage_heading_is_scene_not_photo_wizard():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert "<h1>Relevé → Scene 3D</h1>" in text
    assert "1. Photos" not in text
    assert "2. Relevé" not in text
