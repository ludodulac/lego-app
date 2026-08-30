from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_generated_handoff_explains_backend_resolved_contact_rule() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "VALIDATION DU CONTACT resolved — OBLIGATOIRE" in source
    assert "tolérance backend de raccord métrique est 0,12 m" in source
    assert "POINT de ligne médiane start ou end lui-même" in source
    assert "StairRun.width ne compte JAMAIS comme contact" in source
    assert "min(|x-x0|,|x-x1|,|y-y0|,|y-y1|) <= 0,12" in source
    assert "semantic_anchor_volume_id:null" in source
    assert "CHAQUE relation resolved vers une ancre de volume" in source


def test_resolved_contact_guard_does_not_snap_imported_geometry() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "snapResolved" not in source
    assert "snapToVolume" not in source
    assert "stair.start =" not in source
    assert "stair.end =" not in source
