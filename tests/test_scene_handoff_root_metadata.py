from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "scene-handoff-photo-evidence.js"


def test_generated_scene_handoff_requires_root_id_and_name():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'contient OBLIGATOIREMENT les champs non vides \\"id\\" et \\"name\\"' in source
    assert '\\"id\\":\\"brickhouse-scene\\"' in source
    assert '\\"name\\":\\"BrickHouse architectural scene\\"' in source


def test_scene_import_compatibility_fills_only_missing_root_metadata():
    source = SOURCE.read_text(encoding="utf-8")
    assert "if (typeof clone.id !== 'string' || !clone.id.trim()) clone.id = 'brickhouse-scene';" in source
    assert "if (typeof clone.name !== 'string' || !clone.name.trim()) clone.name = 'BrickHouse architectural scene';" in source
    assert "Do not overwrite any non-empty value supplied by the external model." in source
