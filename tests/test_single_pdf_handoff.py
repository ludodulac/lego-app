from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
ACTIVE_PACKAGE = FRONTEND / "brickhouse-survey-package-v04.js"


def test_photo_page_uses_single_pdf_as_primary_handoff() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    package_src = 'src="./brickhouse-survey-package.js?v=pdf-handoff-0.7-coverage-preflight"'
    assert "Créer le PDF unique à envoyer à l’IA" in html
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in html
    assert package_src in html
    assert html.index(package_src) < html.index('src="./photo-simple.js')


def test_single_pdf_contains_prompts_and_embedded_photo_pages() -> None:
    source = ACTIVE_PACKAGE.read_text(encoding="utf-8")
    assert "PACKAGE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf'" in source
    assert "brickhouse-topology-prompt.txt" in source
    assert "brickhouse-survey-prompt.txt" in source
    assert "makeTextImages" in source
    assert "makePhotoImage" in source
    assert "canvas.toDataURL('image/jpeg'" in source
    assert "pdfFromImages" in source
    assert "application/pdf" in source
    assert "event.stopImmediatePropagation()" in source


def test_single_pdf_uses_cardinal_then_targeted_detail_order() -> None:
    source = ACTIVE_PACKAGE.read_text(encoding="utf-8")
    assert "['front', 'right', 'left', 'rear']" in source
    assert "['detail_1', 'detail_2', 'detail_3', 'detail_4', 'detail_5', 'detail_6']" in source
    assert "captureRole: 'facade_view'" in source
    assert "captureRole: 'targeted_detail'" in source
    assert "orientationAuthority: 'none'" in source
    assert "MAX_PHOTOS_PER_GROUP = 4" in source
    assert "MAX_PHOTOS = 40" in source


def test_targeted_detail_pdf_contract_does_not_invent_facade() -> None:
    source = ACTIVE_PACKAGE.read_text(encoding="utf-8")
    assert "targeted_detail n’ont aucune façade implicite" in source
    assert "facade=null" in source
    assert "image_left_maps_to_facade_offset=null" in source
    assert "ne fabrique jamais une façade" in source
    assert "note utilisateur" in source


def test_single_pdf_requires_survey_output_without_conversation() -> None:
    source = ACTIVE_PACKAGE.read_text(encoding="utf-8")
    assert "produis UNIQUEMENT un ArchitecturalSurvey v0.1 complet" in source
    assert "ne demande aucune confirmation" in source
    assert "brickhouse-survey-result.json" in source
    assert "NE CONSTRUIS PAS DE SCENE" in source


def test_single_pdf_exposes_current_handoff_version() -> None:
    source = ACTIVE_PACKAGE.read_text(encoding="utf-8")
    assert "PDF_HANDOFF_VERSION = 'pdf-handoff-0.4'" in source
    assert "HANDOFF_VERSION=${PDF_HANDOFF_VERSION}" in source
    assert "Handoff ${PDF_HANDOFF_VERSION} prêt" in source
