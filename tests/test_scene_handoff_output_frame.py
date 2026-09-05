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
    assert "text.slice(0, firstBreak + 1)" in frame
    assert "Keep the authoritative v4.3 header as the literal first line" in frame


def test_scene_stage_entry_point_uses_fresh_dedicated_runtime_modules():
    scene = (ROOT / "frontend/scene.html").read_text(encoding="utf-8")
    runtime = (ROOT / "frontend/scene-benchmark-runtime.js").read_text(encoding="utf-8")
    assert "fetch('./photo.html'" not in scene
    assert "document.write" not in scene
    assert "scene-benchmark-runtime.js?v=bh147-scene-runtime-1" in scene
    assert "scene-handoff-stage-lock-v45.js" in runtime
    assert "scene-handoff-output-frame-v46.js" in runtime
    assert 'id="download-scene-handoff"' in scene
