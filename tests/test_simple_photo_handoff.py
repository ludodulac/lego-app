from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_guided_photo_workflow_keeps_required_product_hooks() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    for slot in ("front", "right", "left", "rear"):
        assert f'data-slot="{slot}"' in html
    for slot in ("detail_1", "detail_2", "detail_3", "detail_4", "detail_5", "detail_6"):
        assert f'data-slot="{slot}"' in html
    for element_id in (
        "photos",
        "known-width",
        "notes",
        "studs",
        "external-analysis-file",
        "external-analysis",
        "import-analysis",
        "build-bricks",
        "status",
    ):
        assert f'id="{element_id}"' in html
    assert "photo-simple.js" in html
    assert "brickhouse-survey-package.js?v=pdf-handoff-0.8-scene-source-lock" in html
    assert "brickhouse-single-package.js" not in html
    assert "external-bundle-import.js" in html


def test_external_handoff_active_pdf_package_and_result_file() -> None:
    source = (FRONTEND / "brickhouse-survey-package-v04.js").read_text(encoding="utf-8")
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in source
    assert "brickhouse-survey-result.json" in source
    assert "brickhouse-topology-prompt.txt" in source
    assert "brickhouse-survey-prompt.txt" in source
    assert "makePhotoImage" in source
    assert "pdfFromImages" in source


def test_external_result_bundle_reuses_existing_scene_gate() -> None:
    source = (FRONTEND / "external-bundle-import.js").read_text(encoding="utf-8")
    assert "/api/v1/validate-survey" in source
    assert "brickhouse.pendingArchitecturalSurvey" in source
    assert "button.click()" in source
