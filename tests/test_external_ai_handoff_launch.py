from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMPLE = ROOT / "frontend" / "photo-simple.js"


def test_external_ai_handoff_has_explicit_launch_instruction() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "EXTERNAL_AI_LAUNCH_MESSAGE" in source
    assert "Le fichier Markdown est l’instruction utilisateur principale" in source
    assert "Ne me demande pas ce que je souhaite obtenir" in source
    assert "navigator.clipboard.writeText(EXTERNAL_AI_LAUNCH_MESSAGE)" in source
    assert "ai-launch-instruction-block" in source


def test_primary_handoff_is_direct_markdown_not_zip_dependent() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "brickhouse-analyse-instructions.md" in source
    assert "HANDOFF_SCHEMA_VERSION = 'handoff-0.4'" in source
    assert "combinedInstruction" in source
    assert "# ÉTAPE 1 — TOPOLOGIE MULTI-VUES" in source
    assert "# ÉTAPE 2 — ARCHITECTURAL SURVEY" in source
    assert "# ÉTAPE 3 — SURVEY → SCENE" in source
    assert "downloadTextFile" in source
    assert "brickhouse-external-result.json" in source
    assert "createZip" not in source
    assert "brickhouse-photos-a-analyser.zip" not in source


def test_handoff_keeps_building_generic_and_labels_non_authoritative() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "ne force jamais une photo à correspondre à son libellé" in source
    assert "Le bâtiment peut être non rectangulaire, multi-volume ou atypique" in source
    assert "ne pas imposer la maison benchmark comme modèle général" in source
    assert "guided_base_zones" in source
    assert "slot_view_index" in source
