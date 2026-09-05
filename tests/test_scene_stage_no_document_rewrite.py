from pathlib import Path


def test_scene_stage_does_not_rewrite_another_page():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert "document.open" not in text
    assert "document.write" not in text
    assert "document.close" not in text
