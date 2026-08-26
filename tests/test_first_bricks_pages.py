from pathlib import Path


def test_pages_build_generates_current_five_photo_partial_export() -> None:
    workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")

    assert "tests/fixtures/brickhouse_scene_current.json" in workflow
    assert "frontend/brickhouse-partial-export.json" in workflow
    assert "--allow-partial" in workflow
    assert "partial_preview_roof_omitted" in workflow


def test_first_bricks_entry_loads_published_export_into_progressive_viewer() -> None:
    html = Path("frontend/brickhouse-first-bricks.html").read_text(encoding="utf-8")
    script = Path("frontend/brickhouse-first-bricks.js").read_text(encoding="utf-8")
    scene_html = Path("frontend/scene-viewer.html").read_text(encoding="utf-8")

    assert "Premières briques fiables" in html
    assert "brickhouse-partial-export.json" in script
    assert "brickhouse.pendingExport" in script
    assert "./viewer.html" in script
    assert "brickhouse-first-bricks.html" in scene_html
