from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scene_stage_wires_dedicated_runtime():
    html = (ROOT / "frontend" / "scene.html").read_text(encoding="utf-8")
    runtime = (ROOT / "frontend" / "scene-benchmark-runtime.js").read_text(encoding="utf-8")
    assert './scene-benchmark-runtime.js?v=bh147-scene-runtime-1' in html
    assert "import './scene-handoff-photo-evidence.js?v=scene-runtime-bh147'" in runtime
    assert "import './scene-handoff-stage-lock-v45.js?v=scene-runtime-bh147'" in runtime
    assert "import './scene-handoff-output-frame-v46.js?v=scene-runtime-bh147'" in runtime
    assert "scene-stage-ui.js" not in html
