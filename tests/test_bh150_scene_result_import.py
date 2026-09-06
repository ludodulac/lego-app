from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_HTML = ROOT / "frontend" / "scene.html"
SCENE_IMPORT = ROOT / "frontend" / "scene-result-import.js"


def test_scene_route_exposes_scene_result_import_and_build_controls():
    html = SCENE_HTML.read_text(encoding="utf-8")
    assert 'id="scene-result-file"' in html
    assert 'id="scene-result-json"' in html
    assert 'id="scene-import-result"' in html
    assert 'id="scene-build-bricks"' in html
    assert 'id="scene-build-size"' in html
    assert './scene-result-import.js?v=bh150-scene-result-import-1' in html
    assert 'Scene 3D → LEGO' in html


def test_scene_result_import_validates_against_accepted_survey_before_building():
    source = SCENE_IMPORT.read_text(encoding="utf-8")
    survey_validation = source.index("/api/v1/validate-scene-against-survey")
    scene_validation = source.index("/api/v1/validate-scene", survey_validation + 1)
    build = source.index("/api/v1/build-scene")
    assert survey_validation < scene_validation < build
    assert "brickhouse.lastSceneSurveyValidation" in source
    assert "brickhouse.pendingArchitecturalScene" in source
    assert "brickhouse.pendingExport" in source
    assert "allow_partial: true" in source


def test_scene_result_import_rejects_survey_shaped_payloads_client_side():
    source = SCENE_IMPORT.read_text(encoding="utf-8")
    assert "scene.schema_version !== '0.2'" in source
    assert "'photos' in scene" in source
    assert "'observations' in scene" in source
    assert "'known_measurements' in scene" in source
    assert "Aucune géométrie manquante n’est inventée" in SCENE_HTML.read_text(encoding="utf-8")
