import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_real_house_benchmark_manifest_keeps_five_original_assets():
    manifest = json.loads(
        (ROOT / "frontend/benchmarks/real-house-5/manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["id"] == "real-house-5"
    assert manifest["orientation_authority"] == "capture_hint"
    assert manifest["known_front_width_m"] is None
    assert [photo["path"] for photo in manifest["photos"]] == [
        "01-original.jpg",
        "02-original.jpg",
        "03-original.jpg",
        "04-original.jpg",
        "05-original.jpg",
    ]


def test_real_house_benchmark_loader_is_opt_in_and_preserves_capture_uncertainty():
    loader = (ROOT / "frontend/real-house-benchmark-loader.js").read_text(encoding="utf-8")
    package = (ROOT / "frontend/brickhouse-survey-package.js").read_text(encoding="utf-8")

    assert "if (requestedBenchmark() !== BENCHMARK_ID) return;" in loader
    assert "[1, { slot: 'front', detail: false }]" in loader
    assert "[2, { slot: 'right', detail: false }]" in loader
    assert "[3, { slot: 'rear', detail: false }]" in loader
    assert "[4, { slot: 'detail_1', detail: true }]" in loader
    assert "[5, { slot: 'detail_1', detail: true }]" in loader
    assert "manifest.orientation_authority !== 'capture_hint'" in loader
    assert "orientationCheckbox.checked = false" in loader
    assert "knownWidth.value = ''" in loader
    assert "notes.value = ''" in loader
    assert "real-house-benchmark-loader.js" in package
