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


def test_mobile_shell_keeps_existing_workflow_cards_visible_and_navigable():
    assert "requestedView" not in STATE_JS
    assert "dataset.shellPanel" not in STATE_JS
    assert "[data-shell-panel]{display:none!important}" not in MOBILE_SHELL_CSS
    assert ".panel>h1,.panel>.intro,.panel>.eyebrow{display:none}" not in MOBILE_SHELL_CSS
    assert "#measure-card" not in STATE_JS
    assert "scrollIntoView" not in STATE_JS
