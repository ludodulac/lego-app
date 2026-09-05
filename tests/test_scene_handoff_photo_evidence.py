from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
AUDIT = FRONTEND / "scene-handoff-contract-audit-v44.js"
PACKAGE = FRONTEND / "brickhouse-survey-package.js"


def test_staged_scene_handoff_prefers_single_hybrid_pdf_and_keeps_photo_fallback() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "scene-handoff-0.5-single-hybrid-pdf" in source
    assert "BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in source
    assert "ENTRÉE UNIQUE" in source
    assert "INTERDICTION DE PROJECTION SANS IMAGES" in source
    assert "Ne tente pas de reconstruire la Scene depuis le Survey textuel seul" in source
    assert "Les pages photo sont volontairement placées À LA FIN" in source
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


def test_staged_scene_handoff_keeps_exact_scene_serialization_contract_via_v44_audit() -> None:
    generator = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    package = PACKAGE.read_text(encoding="utf-8")
    assert "${prompt}" in generator
    assert "scene-handoff-contract-audit-v44.js" in package
    assert "EVIDENCE SERIALIZATION — REQUIRED" in audit
    assert "every Scene evidence item is an OBJECT" in audit
    assert '"photo:1"' in audit
    assert "SceneVolume.floors is an integer" in audit
    assert "Platform.width, Platform.depth, Platform.thickness and StairRun.width" in audit
    assert "Terrain uses the canonical terrain.profiles field" in audit
    assert "CERTAIN CHIMNEYS" in audit


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


def test_handoff_preserves_qualitative_terrain_and_certain_chimney_through_v44_audit() -> None:
    generator = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    assert "${prompt}" in generator
    assert "QUALITATIVE TERRAIN" in audit
    assert "terrain.profiles" in audit
    assert "CERTAIN CHIMNEYS" in audit
    assert "ArchitecturalScene v0.2 supports chimneys" in audit


def test_photo_page_loads_single_hybrid_scene_handoff_guard() -> None:
    source = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert "scene-handoff-photo-evidence.js?v=scene-handoff-0.5-single-hybrid-pdf" in source
