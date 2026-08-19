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
