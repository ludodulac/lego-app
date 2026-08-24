import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "frontend" / "benchmarks" / "real-house-5" / "manifest.json"
LOADER = ROOT / "frontend" / "benchmark-fixtures.js"


def test_real_house_benchmark_manifest_has_exactly_five_file_assets() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["id"] == "real-house-5"
    assert manifest["status"] == "awaiting_original_files"
    assert len(manifest["photos"]) == 5
    assert [photo["photo_index"] for photo in manifest["photos"]] == [1, 2, 3, 4, 5]
    for photo in manifest["photos"]:
        path = photo["path"]
        assert path.endswith(".jpg")
        assert not path.startswith("data:")
        assert "base64" not in path.lower()


def test_benchmark_loader_fetches_binary_assets_as_files_without_base64() -> None:
    source = LOADER.read_text(encoding="utf-8")
    assert "response.blob()" in source
    assert "new File([blob]" in source
    assert "toDataURL" not in source
    assert "base64" not in source.lower()
