from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_product_pages_exist_and_link_to_dedicated_viewer() -> None:
    assert (FRONTEND / "index.html").exists()
    assert (FRONTEND / "viewer.html").exists()
    assert "./configurator.html" in read("index.html")
    assert "./photo.html" in read("index.html")
    assert "./viewer.html" in read("configurator.js")
    assert "./viewer.html" in read("photo.js")


def test_generated_export_is_persisted_for_manual() -> None:
    viewer = read("viewer.js")
    instructions = read("instructions.html")
    assert "brickhouse.currentExport" in viewer
    assert "brickhouse.currentExport" in instructions


def test_live_api_is_default_for_user_entry_points() -> None:
    expected = "https://brickhouse-api.onrender.com"
    assert expected in read("configurator.js")
    assert expected in read("photo.js")
    assert expected in read("app.js")


def test_home_exposes_live_service_state() -> None:
    home = read("index.html")
    assert 'id="engine-status"' in home
    assert 'id="api-status"' in home
    assert 'id="vision-status"' in home


def test_photo_import_supports_architectural_scene_and_legacy_analysis() -> None:
    photo = read("photo.js")
    assert "/api/v1/validate-scene" in photo
    assert "/api/v1/validate-analysis" in photo
    assert "architectural-scene.json" in photo
    assert "pendingArchitecturalScene" in photo


def test_external_json_import_extracts_first_complete_object() -> None:
    photo = read("photo.js")
    assert "function cleanExternalJson" in photo
    assert "depth === 0" in photo
    assert "value.slice(start, index + 1)" in photo


def test_viewer_exposes_canonical_architectural_views() -> None:
    html = read("viewer.html")
    viewer = read("viewer.js")
    for control in ('view-front', 'view-rear', 'view-left', 'view-right'):
        assert f'id="{control}"' in html
    assert "function frameCanonicalView" in viewer
    assert "front:new THREE.Vector3(0,.08,-1)" in viewer
    assert "rear:new THREE.Vector3(0,.08,1)" in viewer
    assert "left:new THREE.Vector3(-1,.08,0)" in viewer
    assert "right:new THREE.Vector3(1,.08,0)" in viewer
    assert "perspective:new THREE.Vector3(.9,.65,-1.05)" in viewer
