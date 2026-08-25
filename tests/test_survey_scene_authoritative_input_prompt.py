from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "frontend" / "scene-handoff-photo-evidence.js"


def test_scene_handoff_aligns_prompt_with_photo_evidence_contract() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert "function alignPromptWithPhotoEvidenceContract" in source
    assert "AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO" in source
    assert "Survey reste autoritatif" in source
    assert "PDF sert uniquement à reconstruire la géométrie" in source
    assert "alignPromptWithPhotoEvidenceContract(await response.text())" in source


def test_scene_handoff_rejects_survey_only_prompt_contradictions() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert "AUTORITÉ DE L’ENTRÉE — AUCUN FICHIER SUPPLÉMENTAIRE" in source
    assert "N’exige, ne réclame et ne suppose aucun PDF" in source
    assert "Tu N’AS PAS accès aux photos originales" in source
    assert "contrat Survey → Scene contradictoire avec le handoff photo" in source
    assert "le PDF photo original a été utilisé uniquement comme preuve géométrique complémentaire" in source
