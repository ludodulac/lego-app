from pathlib import Path


PROMPT = Path("frontend/brickhouse-survey-to-scene-prompt.txt")


def test_scene_prompt_uses_profiles_collection_for_terrain():
    text = PROMPT.read_text(encoding="utf-8")
    assert "Terrain utilise `profiles`" in text
    assert "Terrain utilise `facade_grade_profiles`" not in text
    assert 'terrain.kind:"facade_grade_profiles"' in text
    assert "terrain.profiles" in text
