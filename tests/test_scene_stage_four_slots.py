from pathlib import Path


def test_scene_stage_keeps_four_orientation_slots_for_five_photos():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert text.count('class="guided-photo-slot"') == 4
    assert "Gauche · 2 vues" in text
