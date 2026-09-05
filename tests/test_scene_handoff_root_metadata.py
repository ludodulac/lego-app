from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "scene-handoff-photo-evidence.js"
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_generated_scene_handoff_requires_root_id_and_name_through_embedded_prompt():
    source = SOURCE.read_text(encoding="utf-8")
    prompt = PROMPT.read_text(encoding="utf-8")
    assert "${prompt}" in source
    assert '"id"' in prompt
    assert '"name"' in prompt
    assert "brickhouse-scene" in prompt
    assert "BrickHouse architectural scene" in prompt


def test_scene_import_compatibility_fills_only_missing_root_metadata():
    source = SOURCE.read_text(encoding="utf-8")
    assert "if (typeof clone.id !== 'string' || !clone.id.trim()) clone.id = 'brickhouse-scene';" in source
    assert "if (typeof clone.name !== 'string' || !clone.name.trim()) clone.name = 'BrickHouse architectural scene';" in source
    assert "if (typeof clone.id !== 'string' || !clone.id.trim())" in source
    assert "if (typeof clone.name !== 'string' || !clone.name.trim())" in source
