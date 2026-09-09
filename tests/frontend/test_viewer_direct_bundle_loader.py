from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOADER = ROOT / "frontend" / "viewer-load.html"


def test_direct_viewer_loader_is_generic_same_origin_and_uses_pending_export() -> None:
    html = LOADER.read_text(encoding="utf-8")

    assert "params.get('bundle')" in html
    assert "url.origin!==location.origin" in html
    assert "brickhouse.pendingExport" in html
    assert "location.replace('./viewer.html')" in html
    assert "real-house-5" not in html
