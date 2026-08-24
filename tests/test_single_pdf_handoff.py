from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_photo_page_uses_single_pdf_as_primary_handoff() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert "Créer le PDF unique à envoyer à l’IA" in html
    assert "BRICKHOUSE-ANALYSE-COMPLETE.pdf" in html
    assert 'src="./brickhouse-single-package.js"' in html
    assert html.index('src="./brickhouse-single-package.js"') < html.index('src="./photo-simple.js"')


def test_single_pdf_contains_prompts_and_embedded_photo_pages() -> None:
    source = (FRONTEND / "brickhouse-single-package.js").read_text(encoding="utf-8")
    assert "PACKAGE_FILENAME = 'BRICKHOUSE-ANALYSE-COMPLETE.pdf'" in source
    assert "brickhouse-topology-prompt.txt" in source
    assert "brickhouse-survey-prompt.txt" in source
    assert "brickhouse-survey-to-scene-prompt.txt" in source
    assert "makeTextPages" in source
    assert "makePhotoPage" in source
    assert "canvas.toDataURL('image/jpeg'" in source
    assert "pdfFromCanvases" in source
    assert "application/pdf" in source
    assert "event.stopImmediatePropagation()" in source


def test_single_pdf_uses_deterministic_architectural_photo_order() -> None:
    source = (FRONTEND / "brickhouse-single-package.js").read_text(encoding="utf-8")
    assert "['front', 'right', 'left', 'rear', 'front_left', 'front_right']" in source
    assert "orientationAuthority" in source
    assert "user_confirmed" in source
    assert "capture_hint" in source
    assert "PHOTOS, DANS L’ORDRE DU PDF" in source


def test_single_pdf_requires_direct_json_output_without_conversation() -> None:
    source = (FRONTEND / "brickhouse-single-package.js").read_text(encoding="utf-8")
    assert "Ce PDF est l’unique entrée BrickHouse de ce run" in source
    assert "ne demande pas ce que l’utilisateur souhaite" in source
    assert "ne demande pas de confirmation intermédiaire" in source
    assert "brickhouse-external-result.json" in source
    assert '"schema_version": "external-bundle-0.1"' in source


def test_single_pdf_distinguishes_topology_from_complete_survey_and_scene_contracts() -> None:
    source = (FRONTEND / "brickhouse-single-package.js").read_text(encoding="utf-8")
    assert "survey et scene ne sont PAS des résumés de la topologie" in source
    assert "id, name, canonical_frame, photos, observations et relations" in source
    assert "Chaque relation Survey doit contenir id, kind, subject_id, object_id, certainty, statement et evidence" in source
    assert "ne mets jamais directement le résultat de l'étape TOPOLOGIE dans survey ou scene" in source


def test_single_pdf_exposes_handoff_version_in_ui_and_pdf_command() -> None:
    source = (FRONTEND / "brickhouse-single-package.js").read_text(encoding="utf-8")
    assert "PDF_HANDOFF_VERSION = 'pdf-handoff-0.2'" in source
    assert "HANDOFF_VERSION=${PDF_HANDOFF_VERSION}" in source
    assert "Handoff ${PDF_HANDOFF_VERSION} prêt" in source
