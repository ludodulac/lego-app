from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_guided_photo_workflow_keeps_required_legacy_hooks() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    for slot in ("front", "front_left", "left", "rear", "right", "front_right"):
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
    assert "brickhouse-single-package.js" in html
    assert "external-bundle-import.js" in html


def test_external_handoff_is_one_pdf_package_and_one_result_file() -> None:
    source = (FRONTEND / "brickhouse-single-package.js").read_text(encoding="utf-8")
    assert "BRICKHOUSE-ANALYSE-COMPLETE.pdf" in source
    assert "brickhouse-external-result.json" in source
    assert "brickhouse-topology-prompt.txt" in source
    assert "brickhouse-survey-prompt.txt" in source
    assert "brickhouse-survey-to-scene-prompt.txt" in source
    assert "makePhotoPage" in source
    assert "pdfFromCanvases" in source


def test_external_result_bundle_reuses_existing_scene_gate() -> None:
    source = (FRONTEND / "external-bundle-import.js").read_text(encoding="utf-8")
    assert "/api/v1/validate-survey" in source
    assert "brickhouse.pendingArchitecturalSurvey" in source
    assert "button.click()" in source
