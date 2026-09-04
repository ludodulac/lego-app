from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_photo_slot_previews_are_wired_for_guided_and_detail_inputs():
    preview = (ROOT / "frontend/photo-slot-previews.js").read_text(encoding="utf-8")
    package = (ROOT / "frontend/brickhouse-survey-package.js").read_text(encoding="utf-8")

    assert "'.guided-photo-input, .detail-photo-input'" in preview
    assert "selected-photo-previews" in preview
    assert "URL.createObjectURL(file)" in preview
    assert "document.addEventListener('change'" in preview
    assert "renderAll" in preview
    assert "photo-slot-previews.js" in package
    assert package.index("photo-slot-previews.js") < package.index("real-house-benchmark-loader.js")
