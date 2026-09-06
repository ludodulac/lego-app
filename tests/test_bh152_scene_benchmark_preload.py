from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_HTML = ROOT / "frontend" / "scene.html"
PRELOAD_JS = ROOT / "frontend" / "scene-benchmark-candidate-preload.js"
CANDIDATE = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
EXPECTED_SHA = "5cf374b0c8a70bb9823c2e69a1367461d75508f9"


def test_scene_page_wires_validated_candidate_preload_after_import_logic() -> None:
    html = SCENE_HTML.read_text(encoding="utf-8")
    import_tag = "./scene-result-import.js?v=bh150-scene-result-import-1"
    preload_tag = "./scene-benchmark-candidate-preload.js?v=bh152-scene-candidate-preload-1"
    assert import_tag in html
    assert preload_tag in html
    assert html.index(import_tag) < html.index(preload_tag)
    assert "précharge désormais le candidat Scene validé" in html


def test_preload_is_scoped_to_real_house_scene_route_and_pinned_to_bh151_checkpoint() -> None:
    source = PRELOAD_JS.read_text(encoding="utf-8")
    assert "params.get('benchmark') === BENCHMARK_ID" in source
    assert "params.get('stage') === 'scene'" in source
    assert EXPECTED_SHA in source
    assert "raw.githubusercontent.com/ludodulac/lego-app/${VALIDATED_CANDIDATE_SHA}" in source
    assert "brickhouse-scene-real-house-5-candidate" in source
    assert "Importer et vérifier la Scene" in source
    assert "Vous pouvez toujours importer brickhouse-scene-result.json manuellement" in source


def test_pinned_checkpoint_is_the_candidate_validated_by_bh151() -> None:
    candidate = CANDIDATE.read_text(encoding="utf-8")
    assert '"id": "brickhouse-scene-real-house-5-candidate"' in candidate
    assert '"kind": "user_provided"' not in candidate
    assert '"known_measurements"' not in candidate
