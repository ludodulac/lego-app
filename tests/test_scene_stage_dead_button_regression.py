from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scene_button_is_enabled_only_after_runtime_seeds_inputs():
    scene = (ROOT / 'frontend/scene.html').read_text(encoding='utf-8')
    runtime = (ROOT / 'frontend/scene-benchmark-runtime.js').read_text(encoding='utf-8')
    assert '<button id="download-scene-handoff"' in scene
    assert 'disabled>Créer le PDF Relevé → Scene 3D</button>' in scene
    assert "localStorage.setItem('brickhouse.pendingArchitecturalSurvey'" in runtime
    assert 'setInputFiles(input, files)' in runtime
    assert 'button.disabled = false' in runtime
    assert "Prêt : créez le PDF Relevé → Scene 3D." in runtime


def test_scene_page_no_longer_loads_photo_shell_dependency_chain():
    scene = (ROOT / 'frontend/scene.html').read_text(encoding='utf-8')
    assert 'brickhouse-survey-package.js' not in scene
    assert 'photo-shell-loader.js' not in scene
    assert 'real-house-benchmark-loader.js' not in scene
    assert 'scene-stage-ui.js' not in scene
