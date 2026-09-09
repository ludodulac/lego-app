from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_validated_scene_build_uses_rich_partial_endpoint_and_viewer_handoff() -> None:
    source = (ROOT / "frontend" / "scene-build-direct.js").read_text(encoding="utf-8")
    package = (ROOT / "frontend" / "brickhouse-survey-package.js").read_text(encoding="utf-8")

    assert "/api/v1/validate-scene" in source
    assert "/api/v1/build-scene" in source
    assert "allow_partial: true" in source
    assert "brickhouse.pendingExport" in source
    assert "./viewer.html" in source
    assert "scene-build-direct.js" in package
    assert "real-house-5" not in source
