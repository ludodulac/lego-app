from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "scene-handoff-photo-evidence.js"
AUDIT = ROOT / "frontend" / "scene-handoff-contract-audit-v44.js"
PACKAGE = ROOT / "frontend" / "brickhouse-survey-package.js"


def test_generated_scene_handoff_requires_root_id_and_name_through_v44_audit():
    source = SOURCE.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    package = PACKAGE.read_text(encoding="utf-8")
    assert "${prompt}" in source
    assert "scene-handoff-contract-audit-v44.js" in package
    assert "ROOT METADATA — REQUIRED" in audit
    assert 'non-empty "id" and "name" fields' in audit
    assert "brickhouse-scene" in audit
    assert "BrickHouse architectural scene" in audit


def test_scene_import_compatibility_fills_only_missing_root_metadata():
    source = SOURCE.read_text(encoding="utf-8")
    assert "if (typeof clone.id !== 'string' || !clone.id.trim()) clone.id = 'brickhouse-scene';" in source
    assert "if (typeof clone.name !== 'string' || !clone.name.trim()) clone.name = 'BrickHouse architectural scene';" in source
    assert "if (typeof clone.id !== 'string' || !clone.id.trim())" in source
    assert "if (typeof clone.name !== 'string' || !clone.name.trim())" in source
