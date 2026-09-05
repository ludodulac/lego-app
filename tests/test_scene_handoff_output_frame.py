from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_output_frame_runs_after_v45_stage_lock():
    package = (ROOT / "frontend/brickhouse-survey-package.js").read_text(encoding="utf-8")
    lock = "scene-handoff-stage-lock-v45.js"
    frame = "scene-handoff-output-frame-v46.js"
    assert lock in package
    assert frame in package
    assert package.index(lock) < package.index(frame)


def test_output_frame_keeps_v43_header_first_and_rejects_survey_output():
    frame = (ROOT / "frontend/scene-handoff-output-frame-v46.js").read_text(encoding="utf-8")
    assert "OUTPUT_TARGET=ArchitecturalScene v0.2" in frame
    assert "OUTPUT_FILE=brickhouse-scene-result.json" in frame
    assert 'schema_version="0.1"' in frame
    assert '"photos", "observations" or "known_measurements"' in frame
    assert "brickhouse-survey-result.json" in frame
    assert 'schema_version="0.2"' in frame
    assert "firstBreak + 1" in frame
    assert "rawPrompt.startsWith" not in frame


def test_scene_stage_entry_point_forces_fresh_runtime_modules():
    scene = (ROOT / "frontend/scene.html").read_text(encoding="utf-8")
    assert "fetch('./photo.html', { cache: 'no-store' })" in scene
    assert "scene-stage-4.6-output-frame" in scene
    assert "scene-stage-bh143-fresh" in scene
    assert "document.write(html)" in scene
