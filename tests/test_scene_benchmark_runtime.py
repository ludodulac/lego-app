from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scene_page_uses_dedicated_runtime_and_has_explicit_action():
    scene = (ROOT / 'frontend/scene.html').read_text(encoding='utf-8')
    assert 'scene-benchmark-runtime.js?v=bh147-scene-runtime-1' in scene
    assert 'brickhouse-survey-package.js' not in scene
    assert 'scene-stage-ui.js' not in scene
    assert 'Créer le PDF Relevé → Scene 3D' in scene
    assert 'id="download-scene-handoff"' in scene
    assert 'disabled' in scene


def test_scene_runtime_seeds_frozen_survey_and_exact_five_photo_mapping():
    runtime = (ROOT / 'frontend/scene-benchmark-runtime.js').read_text(encoding='utf-8')
    assert 'accepted-survey-v0.1.json' in runtime
    assert "[1, 'front']" in runtime
    assert "[2, 'right']" in runtime
    assert "[3, 'left']" in runtime
    assert "[4, 'left']" in runtime
    assert "[5, 'rear']" in runtime
    assert 'count !== 5' in runtime
    assert "localStorage.setItem('brickhouse.pendingArchitecturalSurvey'" in runtime
    assert 'valid_for_scene_fusion: true' in runtime
    assert "source: 'accepted_repo_checkpoint'" in runtime
    assert 'button.disabled = false' in runtime


def test_scene_runtime_preserves_output_locks_and_pdf_generator():
    runtime = (ROOT / 'frontend/scene-benchmark-runtime.js').read_text(encoding='utf-8')
    for required in (
        'scene-handoff-source-lock.js',
        'scene-handoff-contract-audit-v44.js',
        'scene-handoff-stage-lock-v45.js',
        'scene-handoff-output-frame-v46.js',
        'scene-handoff-photo-evidence.js',
    ):
        assert required in runtime
    generator = (ROOT / 'frontend/scene-handoff-photo-evidence.js').read_text(encoding='utf-8')
    assert "BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf" in generator
    assert "#download-scene-handoff" in generator
