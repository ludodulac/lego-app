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


def test_guided_capture_supports_base_views_plus_targeted_extras() -> None:
    html = read("photo.html")
    simple = read("photo-simple.js")
    assert 'id="guided-extra-photos"' in html
    assert "6 vues de base" in html
    assert "Jusqu’à 6 vues supplémentaires" in html
    assert "MAX_TOTAL_PHOTOS = 12" in simple
    assert "MAX_EXTRA_PHOTOS = 6" in simple
    assert "targeted_extra" in simple
    assert "few_high_value_views_plus_targeted_extras" in simple


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


def test_topology_and_survey_prompts_use_adaptive_photo_coverage() -> None:
    topology = read("brickhouse-topology-prompt.txt")
    survey = read("brickhouse-survey-prompt.txt")
    assert "TOPOLOGIQUE INTERACTIVE v0.5" in topology
    assert "STRATÉGIE DE COUVERTURE — QUALITÉ AVANT QUANTITÉ" in topology
    assert "4 à 6 vues générales" in topology
    assert "COMMENT DEMANDER UNE VUE SUPPLÉMENTAIRE" in topology
    assert "capture_assessment" in topology
    assert "RELEVÉ ARCHITECTURAL v1.8" in survey
    assert "DENSITÉ DE COUVERTURE" in survey
    assert "quantité de photos jamais confondue avec certitude architecturale" in survey
    assert "une volée qui disparaît derrière un mur ne prouve PAS" in survey
    assert "zone occultée" in survey
    assert "IDENTITÉ STABLE DES PRIMITIVES" in survey


def test_survey_extension_prompt_supports_append_only_refinement() -> None:
    prompt = read("brickhouse-survey-extension-prompt.txt")
    assert "ARCHITECTURALSURVEY v0.5" in prompt
    assert "refines_observation_id" in prompt
    assert "unproven → plausible → certain" in prompt
    assert "jamais `certain`" in prompt
    assert "workflow de correction explicite" in prompt


def test_survey_to_scene_prompt_matches_current_generic_v24_contract() -> None:
    prompt = read("brickhouse-survey-to-scene-prompt.txt")
    assert "PROMPT DE RECONSTRUCTION SURVEY → SCENE v2.4" in prompt
    assert "PORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE" in prompt
    assert "GÉOMÉTRIE NON ORTHOGONALE ET ARCHITECTURES ATYPIQUES" in prompt
    assert "Ne redresse jamais silencieusement" in prompt
    assert "Une seule photo" in prompt
    assert "RAFFINEMENTS APPEND-ONLY DU SURVEY" in prompt
    assert "refines_observation_id" in prompt
    assert "observation raffinée reste une provenance historique" in prompt
    assert "VOLUMES ET PORTÉE DES INFORMATIONS" in prompt
    assert "visibility[]` peut porter `volume_id`" in prompt
    assert "Platform` peut porter `host_volume_id`" in prompt
    assert "SÉMANTIQUE EXACTE DES COORDONNÉES EXTÉRIEURES" in prompt
    assert "AXE CENTRAL" in prompt
    assert "INCERTITUDE DES STRUCTURES EXTÉRIEURES" in prompt
    assert "relation `plausible` ou `unproven`" in prompt
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


def test_viewer_exposes_final_fidelity_issues() -> None:
    html = read("viewer.html")
    viewer = read("viewer.js")
    styles = read("styles.css")
    assert 'id="fidelity-card"' in html
    assert 'id="fidelity-list"' in html
    assert "function updateFidelity" in viewer
    assert "b.fidelity_issues" in viewer
    assert "low_confidence_exterior_geometry" not in viewer  # UI stays generic to issue codes.
    assert "#fidelity-card" in styles


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
