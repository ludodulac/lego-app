import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_HANDOFF = ROOT / "frontend" / "scene-handoff-photo-evidence.js"
PHOTO_HTML = ROOT / "frontend" / "photo.html"
CHECKPOINT = ROOT / "frontend" / "benchmarks" / "real-house-5" / "accepted-survey-checkpoint.json"


def test_scene_handoff_prefers_one_hybrid_pdf_with_text_then_photos():
    source = SCENE_HANDOFF.read_text(encoding="utf-8")

    assert "BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf" in source
    assert "scene-handoff-0.5-single-hybrid-pdf" in source
    assert "PDF HYBRIDE UNIQUE" in source
    assert "LES PAGES SUIVANTES SONT LES PHOTOS" in source
    assert "texte extractible au début" in source
    assert "photos sont placées à la fin" in source

    text_pages = source.index("const pages = makeTextPages(handoff)")
    photo_pages = source.index("pages.push(await makePhotoPage")
    assert text_pages < photo_pages


def test_scene_handoff_pdf_contains_native_text_and_jpeg_resources():
    source = SCENE_HANDOFF.read_text(encoding="utf-8")

    assert "/Subtype /Type1 /BaseFont /Helvetica" in source
    assert ") Tj" in source
    assert "/Filter /DCTDecode" in source
    assert "new Blob([concat(chunks)], { type: 'application/pdf' })" in source


def test_scene_handoff_keeps_conservative_two_file_fallback():
    source = SCENE_HANDOFF.read_text(encoding="utf-8")

    assert "BRICKHOUSE-SURVEY-TO-SCENE.txt" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in source
    assert "if (!records.length)" in source
    assert "fallback" in source.lower()


def test_scene_import_compatibility_normalization_is_preserved():
    source = SCENE_HANDOFF.read_text(encoding="utf-8")

    assert "normalizeExternalScene" in source
    assert "platform.thickness" in source
    assert "clone.terrain.profiles" in source
    assert "clone.appearance" in source
    assert "normalizeSceneTextareaBeforeImport" in source


def test_photo_page_still_loads_scene_handoff_module():
    html = PHOTO_HTML.read_text(encoding="utf-8")
    assert "./scene-handoff-photo-evidence.js" in html


def test_real_house_accepted_survey_checkpoint_is_frozen_for_downstream_work():
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))

    assert checkpoint["benchmark_id"] == "real-house-5"
    assert checkpoint["stage"] == "photos_to_survey"
    assert checkpoint["status"] == "accepted"
    assert checkpoint["survey_schema_version"] == "0.1"
    assert checkpoint["survey_sha256"] == "b19ed423d24d640d6fe8d5ea30102bb6da189684abcc75297a98d1cc9a1ede9a"
    assert checkpoint["invariants"]["photo_facades"] == ["front", "right", "left", "left", "rear"]
    assert checkpoint["invariants"]["known_measurements_count"] == 0
    assert checkpoint["invariants"]["observation_count"] == 19
    assert checkpoint["invariants"]["relation_count"] == 4
    assert checkpoint["next_stage"] == "survey_to_scene"
    assert "Do not rerun Photos -> Survey" in checkpoint["rerun_policy"]
