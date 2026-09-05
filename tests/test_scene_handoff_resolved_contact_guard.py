from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_generated_handoff_embeds_prompt_with_backend_resolved_contact_rule() -> None:
    generator = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    prompt = (FRONTEND / "brickhouse-survey-to-scene-prompt.txt").read_text(encoding="utf-8")
    assert "${prompt}" in generator
    assert "VALIDATION DU CONTACT" in prompt
    assert "0,12 m" in prompt
    assert "StairRun.width" in prompt
    assert "semantic_anchor_volume_id" in prompt
    assert "geometry_status" in prompt


def test_resolved_contact_guard_does_not_snap_imported_geometry() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "snapResolved" not in source
    assert "snapToVolume" not in source
    assert "stair.start =" not in source
    assert "stair.end =" not in source
