from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "frontend" / "styles.css"


def test_desktop_viewer_is_capped_to_the_browser_viewport() -> None:
    source = STYLES.read_text(encoding="utf-8")
    assert ".viewer-wrap { position: sticky; top: 0; align-self: start;" in source
    assert "height: 100vh; min-height: 0; overflow: hidden;" in source


def test_mobile_viewer_restores_document_flow() -> None:
    source = STYLES.read_text(encoding="utf-8")
    mobile = source.split("@media (max-width: 760px)", 1)[1]
    assert ".viewer-wrap { position: relative; top: auto; align-self: stretch; height: 58vh; min-height: 58vh; }" in mobile
