from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMPLE = ROOT / "frontend" / "photo-simple.js"


def test_external_ai_handoff_has_explicit_launch_instruction() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "EXTERNAL_AI_LAUNCH_MESSAGE" in source
    assert "Ne me demande pas quel type d’analyse je souhaite" in source
    assert "00-LIRE-ET-ANALYSER.txt" in source
    assert "00-CONSIGNE-A-COLLER-DANS-LE-CHAT.txt" in source
    assert "navigator.clipboard.writeText(EXTERNAL_AI_LAUNCH_MESSAGE)" in source
    assert "ai-launch-instruction-block" in source


def test_zip_entry_point_is_imperative_and_manifest_carries_launch_instruction() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "INSTRUCTION PRINCIPALE — À EXÉCUTER IMMÉDIATEMENT" in source
    assert "Ce fichier définit la tâche demandée par l’utilisateur" in source
    assert "instructions/01-topologie.txt → instructions/02-survey.txt → instructions/03-survey-vers-scene.txt" in source
    assert "schema_version: 'handoff-0.3'" in source
    assert "launch_instruction: EXTERNAL_AI_LAUNCH_MESSAGE" in source
    assert "brickhouse-external-result.json" in source
