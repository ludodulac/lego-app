from pathlib import Path


PROMPT = Path("frontend/brickhouse-survey-to-scene-prompt.txt")


def test_scene_prompt_uses_profiles_collection_for_terrain():
    text = PROMPT.read_text(encoding="utf-8")
    assert "Terrain utilise `profiles`" in text
    assert "Terrain utilise `facade_grade_profiles`" not in text
    assert 'terrain.kind:"facade_grade_profiles"' in text
    assert "terrain.profiles" in text


def test_scene_prompt_interprets_qualitative_slope_direction_semantically():
    text = PROMPT.read_text(encoding="utf-8")
    assert "sans dépendre d’un token exact" in text
    assert "rises_front_to_rear" in text
    assert "front_to_rear_up" in text
    assert "Ne réécris pas le Survey" in text
    assert "n’invente aucune direction" in text
