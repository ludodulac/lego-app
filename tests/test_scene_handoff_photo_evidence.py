from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_staged_scene_handoff_prefers_single_hybrid_pdf_and_keeps_photo_fallback() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "scene-handoff-0.5-single-hybrid-pdf" in source
    assert "BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in source
    assert "ENTRÉE UNIQUE" in source
    assert "INTERDICTION DE PROJECTION SANS IMAGES" in source
    assert "Ne tente pas de reconstruire la Scene depuis le Survey textuel seul" in source
    assert "photos sont volontairement placées À LA FIN" in source
    assert "Survey" in source and "source de vérité" in source
    assert "if (!records.length)" in source


def test_scene_prompt_source_matches_photo_evidence_contract() -> None:
    source = (FRONTEND / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")
    assert "AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO" in source
    assert "BRICKHOUSE-SURVEY-TO-SCENE.txt" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in source
    assert "Le PDF ne doit jamais refaire, corriger, renommer ou contredire le Survey validé" in source
    assert "down_slope_direction" in source
    assert "pitch_degrees` peut rester `null` indépendamment" in source
    assert "AUTORITÉ DE L’ENTRÉE — AUCUN FICHIER SUPPLÉMENTAIRE" not in source
    assert "Tu N’AS PAS accès aux photos originales" not in source
    assert "aucune dépendance à des photos/PDF/fichiers externes n’a été introduite" not in source


def test_targeted_detail_cards_have_explicit_layout() -> None:
    css = (FRONTEND / "photo.css").read_text(encoding="utf-8")
    assert ".detail-photo-slot{display:grid" in css
    assert ".detail-photo-slot>strong{display:block" in css
    assert ".detail-photo-slot>span{display:block" in css
    assert ".detail-photo-note" in css


def test_staged_scene_handoff_keeps_exact_scene_serialization_contract_in_embedded_prompt() -> None:
    generator = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    prompt = (FRONTEND / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")
    assert "CONTRAT DE SÉRIALISATION — OBLIGATOIRE" in generator
    assert "${prompt}" in generator
    assert 'Chaque evidence Scene est un OBJET exactement de la forme' in prompt
    assert 'N’écris jamais une chaîne comme `"photo:1"`' in prompt
    assert "SceneVolume.floors" in prompt
    assert "Platform.width" in prompt and "Platform.depth" in prompt and "Platform.thickness" in prompt
    assert "StairRun.width" in prompt
    assert "Terrain" in prompt
    assert "chimneys" in prompt


def test_external_scene_import_has_conservative_shape_normalizer() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "function normalizeEvidenceList" in source
    assert "function normalizeExternalScene" in source
    assert "function unwrapPositiveScalarPropertyValue" in source
    assert "^photo:(\\d+)$" in source
    assert "volume.floors.value" in source
    assert "platform.width = unwrapPositiveScalarPropertyValue(platform.width)" in source
    assert "platform.depth = unwrapPositiveScalarPropertyValue(platform.depth)" in source
    assert "platform.thickness = unwrapPositiveScalarPropertyValue(platform.thickness)" in source
    assert "stair.width = unwrapPositiveScalarPropertyValue(stair.width)" in source
    assert "platform.thickness = Number(platform.height)" in source
    assert "clone.terrain.profiles = clone.terrain.facade_grade_profiles" in source
    assert "delete clone.terrain.facade_grade_profiles" in source
    assert "clone.appearance = {}" in source
    assert "normalizeSceneTextareaBeforeImport" in source


def test_scalar_metric_normalizer_is_targeted_and_positive_only() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "Number.isFinite(numeric) && numeric > 0 ? numeric : value" in source
    assert "platform.width = unwrapPositiveScalarPropertyValue(platform.width)" in source
    assert "platform.depth = unwrapPositiveScalarPropertyValue(platform.depth)" in source
    assert "platform.thickness = unwrapPositiveScalarPropertyValue(platform.thickness)" in source
    assert "stair.width = unwrapPositiveScalarPropertyValue(stair.width)" in source
    assert "opening.width = unwrapPositiveScalarPropertyValue" not in source
    assert "volume.width = unwrapPositiveScalarPropertyValue" not in source


def test_handoff_preserves_qualitative_terrain_and_certain_chimney_through_v43_prompt() -> None:
    generator = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    prompt = (FRONTEND / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")
    assert "${prompt}" in generator
    assert "terrain.profiles" in prompt
    assert "PRÉSERVATION" in prompt or "chimney" in prompt.lower()
    assert "chimney" in prompt.lower()


def test_photo_page_loads_single_hybrid_scene_handoff_guard() -> None:
    source = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert "scene-handoff-photo-evidence.js?v=scene-handoff-0.5-single-hybrid-pdf" in source
