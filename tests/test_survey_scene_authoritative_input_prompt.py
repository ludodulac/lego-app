from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "frontend" / "scene-handoff-photo-evidence.js"
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_handoff_aligns_prompt_with_single_pdf_photo_evidence_contract() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert "function alignPromptWithSinglePdfContract" in source
    assert "AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO" in source
    assert "UN SEUL PDF hybride" in source
    assert "source de vérité" in source
    assert "alignPromptWithSinglePdfContract(rawPrompt)" in source


def test_scene_handoff_replaces_v43_photo_authority_without_weakening_it() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    prompt = PROMPT.read_text(encoding="utf-8")
    assert "AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO" in prompt
    assert "AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO" in source
    assert "/AUTORITÉ DES ENTRÉES — SURVEY \\+ PREUVES PHOTO" in source
    assert "PORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE" in source
    assert "contrat Survey → Scene non aligné avec le PDF hybride unique" in source
    assert "ne modifie jamais un fait Survey certain" in source
