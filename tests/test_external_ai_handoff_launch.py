from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMPLE = ROOT / "frontend" / "photo-simple.js"


def test_external_ai_handoff_has_explicit_single_turn_launch_instruction() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "EXTERNAL_AI_LAUNCH_MESSAGE" in source
    assert "mode mono-tour" in source
    assert "Ne réponds pas par une analyse intermédiaire" in source
    assert "ne demande aucune confirmation" in source
    assert "brickhouse-external-result.json" in source
    assert "navigator.clipboard.writeText(EXTERNAL_AI_LAUNCH_MESSAGE)" in source
    assert "ai-launch-instruction-block" in source


def test_primary_handoff_is_direct_text_not_zip_dependent() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "00-BRICKHOUSE-COMMANDE-A-ENVOYER.txt" in source
    assert "HANDOFF_SCHEMA_VERSION = 'handoff-0.6'" in source
    assert "execution_mode: 'single_turn_file_output'" in source
    assert "combinedInstruction" in source
    assert "ÉTAPE 1 — TOPOLOGIE MULTI-VUES" in source
    assert "ÉTAPE 2 — ARCHITECTURAL SURVEY" in source
    assert "ÉTAPE 3 — SURVEY → SCENE" in source
    assert "text/plain;charset=utf-8" in source
    assert "downloadTextFile" in source
    assert "createZip" not in source
    assert "brickhouse-photos-a-analyser.zip" not in source


def test_handoff_forbids_old_result_as_input_and_conversation_detours() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "forbidden_context_files: ['brickhouse-external-result.json']" in source
    assert "Ne joignez PAS un ancien brickhouse-external-result.json" in source
    assert "ignore tout ancien brickhouse-external-result.json" in source
    assert "ne propose pas rénovation, plan LEGO" in source
    assert "ne t’arrête pas après la topologie ou le Survey" in source
    assert "La réponse de chat finale doit être minimale" in source


def test_handoff_distinguishes_capture_hints_from_confirmed_orientations() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "confirm-guided-orientations" in source
    assert "orientation_semantics" in source
    assert "slot_labels_are_user_confirmed" in source
    assert "orientation_authority" in source
    assert "user_confirmed" in source
    assert "capture_hint" in source
    assert "ORIENTATION CONFIRMÉE PAR L’UTILISATEUR" in source
    assert "ORIENTATION NON CONFIRMÉE" in source


def test_handoff_keeps_building_generic() -> None:
    source = SIMPLE.read_text(encoding="utf-8")
    assert "Le bâtiment peut être non rectangulaire, multi-volume ou atypique" in source
    assert "ne pas imposer la maison benchmark comme modèle général" in source
    assert "guided_base_zones" in source
    assert "slot_view_index" in source
