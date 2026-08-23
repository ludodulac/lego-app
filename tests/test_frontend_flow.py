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


def test_external_ai_workflow_supports_json_files_and_validated_survey_download() -> None:
    html = read("photo.html")
    survey = read("survey-import.js")
    assert 'id="external-analysis-file"' in html
    assert 'accept="application/json,.json"' in html
    assert 'id="download-survey"' in html
    assert "await file.text()" in survey
    assert "currentValidatedSurvey" in survey
    assert "architectural-survey-v0.1.json" in survey
    assert "new Blob" in survey


def test_validated_survey_can_be_explicitly_replaced_after_user_correction() -> None:
    html = read("photo.html")
    survey = read("survey-import.js")
    assert 'id="replace-survey"' in html
    assert "replaceMode = true" in survey
    assert "replacing = replaceMode && Boolean(baseSurvey)" in survey
    assert "replaced: replacing" in survey
    assert "ArchitecturalSurvey corrigé valide et actif" in survey
    assert "localStorage.removeItem('brickhouse.pendingArchitecturalScene')" in survey
    assert "localStorage.removeItem('brickhouse.pendingExport')" in survey


def test_scene_import_is_gated_against_pending_validated_survey() -> None:
    survey_import = read("survey-import.js")
    gate = read("scene-survey-gate.js")
    assert "import './scene-survey-gate.js'" in survey_import
    assert "brickhouse.pendingArchitecturalSurvey" in gate
    assert "/api/v1/validate-scene-against-survey" in gate
    assert "valid_for_projection" in gate
    assert "Scène refusée par le Survey" in gate


def test_validated_scene_gate_builds_the_rich_scene_and_opens_viewer() -> None:
    gate = read("scene-survey-gate.js")
    assert "currentSceneBuildPayload" in gate
    assert "gateBuild.disabled = !buildable" in gate
    assert "const scene = payload?.scene ?? null" in gate
    assert "`${base}/api/v1/build-scene`" in gate
    assert "scene," in gate
    assert "brickhouse.pendingArchitecturalScene" in gate
    assert "brickhouse.pendingExport" in gate
    assert "window.location.href = './viewer.html'" in gate
    assert "Étape suivante : cliquez sur « Construire cette proposition »" in gate


def test_survey_to_scene_prompt_matches_current_generic_v21_contract() -> None:
    prompt = read("brickhouse-survey-to-scene-prompt.txt")
    assert "PROMPT DE RECONSTRUCTION SURVEY → SCENE v2.1" in prompt
    assert "PORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE" in prompt
    assert "GÉOMÉTRIE NON ORTHOGONALE ET ARCHITECTURES ATYPIQUES" in prompt
    assert "Ne redresse jamais silencieusement" in prompt
    assert "Une seule photo" in prompt
    assert "VOLUMES ET PORTÉE DES INFORMATIONS" in prompt
    assert "visibility[]` peut porter `volume_id`" in prompt
    assert "Une entrée legacy sans `volume_id`" in prompt
    assert "SceneRoof.type` autorise" in prompt
    assert "type de toiture réel conservé même s’il est non supporté en LEGO" in prompt


def test_viewer_exposes_canonical_architectural_views() -> None:
    html = read("viewer.html")
    viewer = read("viewer.js")
    for control in ('view-front', 'view-rear', 'view-left', 'view-right'):
        assert f'id="{control}"' in html
    assert "function frameCanonicalView" in viewer
    assert "front:new THREE.Vector3(0,0,1)" in viewer
    assert "rear:new THREE.Vector3(0,0,-1)" in viewer
    assert "left:new THREE.Vector3(-1,0,0)" in viewer
    assert "right:new THREE.Vector3(1,0,0)" in viewer
    assert "perspective:new THREE.Vector3(.9,.65,1.05)" in viewer


def test_named_architectural_views_preserve_canonical_handedness() -> None:
    viewer = read("viewer.js")
    assert "camera.up.copy(up)" in viewer
    assert "camera.lookAt(center)" in viewer
    assert "new THREE.Vector3(0,1,0)" in viewer
    assert "modelGroup.scale.z=-1" in viewer.replace(" ", "")
    assert "scale.x=-1" not in viewer.replace(" ", "")
    assert "scaleX(-1)" not in viewer
    assert "world (x,z,-y)" in viewer


def test_viewer_uses_exported_architectural_appearance() -> None:
    viewer = read("viewer.js")
    assert "function applyAppearance" in viewer
    assert "a.roof?.color" in viewer
    assert "setPaletteColor('roof_tile',roof)" in viewer
    assert "applyAppearance(b);clearModel()" in viewer
    assert "dark_gray" in viewer
