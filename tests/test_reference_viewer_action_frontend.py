from pathlib import Path


def test_viewer_can_load_generated_five_photo_reference_through_existing_pending_handoff():
    html = Path("frontend/viewer.html").read_text(encoding="utf-8")
    source = Path("frontend/reference-loader.js").read_text(encoding="utf-8")

    assert 'id="load-reference-house"' in html
    assert "Charger la maison des 5 photos" in html
    assert '<script type="module" src="./reference-loader.js"></script>' in html
    assert "fetch('./brickhouse-partial-export.json',{cache:'no-store'})" in source
    assert "localStorage.setItem('brickhouse.pendingExport',JSON.stringify(bundle))" in source
    assert "window.location.reload()" in source
    assert "bundle?.assembly_plan?.steps?.length>0" in source
