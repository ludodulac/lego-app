from pathlib import Path


def test_scene_stage_import_control_is_internal_only():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    assert 'class="hidden-contract" aria-hidden="true"' in text
    assert '>Importer le JSON<' not in text
