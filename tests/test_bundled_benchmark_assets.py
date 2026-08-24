import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
MANIFEST = BENCHMARK / "manifest.json"
LOADER = ROOT / "frontend" / "benchmark-fixtures.js"


def test_real_house_benchmark_manifest_has_exactly_five_file_assets() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["id"] == "real-house-5"
    assert manifest["status"] == "ready"
    assert manifest["asset_policy"] == "binary_files_only_no_base64"
    assert len(manifest["photos"]) == 5
    assert [photo["photo_index"] for photo in manifest["photos"]] == [1, 2, 3, 4, 5]

    for photo in manifest["photos"]:
        path = photo["path"]
        assert path.endswith(".jpg")
        assert not path.startswith("data:")
        assert "base64" not in path.lower()

        asset = BENCHMARK / path
        assert asset.is_file()
        payload = asset.read_bytes()
        assert len(payload) == photo["size_bytes"]
        assert hashlib.sha256(payload).hexdigest() == photo["sha256"]
        assert payload[:2] == b"\xff\xd8"
        assert payload[-2:] == b"\xff\xd9"


def test_benchmark_loader_fetches_binary_assets_as_files_without_base64() -> None:
    source = LOADER.read_text(encoding="utf-8")
    assert "response.blob()" in source
    assert "new File([blob]" in source
    assert "toDataURL" not in source
    assert "base64" not in source.lower()
