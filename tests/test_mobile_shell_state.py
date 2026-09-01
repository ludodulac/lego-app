from pathlib import Path


STATE_JS = Path("frontend/mobile-shell-state.js").read_text(encoding="utf-8")
SCENE_BUILD_JS = Path("frontend/scene-build.js").read_text(encoding="utf-8")
MOBILE_SHELL_CSS = Path("frontend/mobile-shell.css").read_text(encoding="utf-8")


def test_shell_state_reuses_existing_survey_scene_and_build_signals():
    assert "brickhouse.pendingArchitecturalSurvey" in STATE_JS
    assert "#scene-handoff-home" in STATE_JS
    assert "#json-preview" in STATE_JS
    assert "schema_version === '0.2'" in STATE_JS
    assert "#build-bricks" in STATE_JS
    assert "MutationObserver" in STATE_JS


def test_shell_state_is_loaded_additively_from_existing_scene_build_module():
    assert "import './mobile-shell-state.js';" in SCENE_BUILD_JS
    assert "import './scene-required-inputs.js';" in SCENE_BUILD_JS
    assert "prepareConservativePartialScene" in SCENE_BUILD_JS
    assert "window.location.href = './viewer.html';" in SCENE_BUILD_JS


def test_shell_progress_has_active_and_complete_visual_states():
    assert ".shell-progress-step.is-active" in MOBILE_SHELL_CSS
    assert ".shell-progress-step.is-complete" in MOBILE_SHELL_CSS
    assert ".mobile-shell-nav a.is-active" in MOBILE_SHELL_CSS


def test_shell_exposes_contextual_next_action_without_parallel_workflow_state():
    assert "#shell-state-card" in STATE_JS
    assert "État de votre maison" in STATE_JS
    assert "Survey validé" in STATE_JS
    assert "Scene reçue" in STATE_JS
    assert "Maquette prête à construire" in STATE_JS
    assert "#survey-handoff-card" in STATE_JS
    assert "#analysis-panel" in STATE_JS
    assert "#build-ready-card" in STATE_JS
    assert "card.id = 'build-ready-card'" in SCENE_BUILD_JS
    assert ".shell-state-card" in MOBILE_SHELL_CSS


def test_mobile_focus_mode_keeps_one_workflow_panel_visible_without_replacing_state():
    assert "window.matchMedia('(max-width: 620px)')" in STATE_JS
    assert "dataset.shellPanel" in STATE_JS
    assert "requestedView" in STATE_JS
    assert "#detail-photo-grid" in STATE_JS
    assert "#measure-card" in STATE_JS
    assert "viewForTarget" in STATE_JS
    assert "scrollIntoView" in STATE_JS
    assert "[data-shell-panel]{display:none!important}" in MOBILE_SHELL_CSS
    assert "[data-shell-panel].is-shell-view{display:block!important}" in MOBILE_SHELL_CSS
    assert ".future-card{display:none!important}" in MOBILE_SHELL_CSS


def test_optional_detail_capture_is_a_mobile_disclosure_not_a_second_long_panel():
    assert "detailCaptureOpen" in STATE_JS
    assert "#shell-detail-toggle" in STATE_JS
    assert "detail-capture-card" in STATE_JS
    assert "aria-expanded" in STATE_JS
    assert "Ajouter des détails facultatifs" in STATE_JS
    assert ".shell-detail-card.is-shell-view:not(.is-shell-detail-open){display:none!important}" in MOBILE_SHELL_CSS
    assert ".shell-detail-toggle{display:block" in MOBILE_SHELL_CSS
