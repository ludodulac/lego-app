from pathlib import Path


def test_scene_stage_button_is_unambiguous():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert "Créer le PDF unique Survey → Scene" in text
