from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "frontend" / "scene-survey-gate.js"


def test_scene_gate_puts_projection_blocker_in_primary_status() -> None:
    source = GATE.read_text(encoding="utf-8")
    assert "Projection M0 bloquée : ${blockers.join(' ')}" in source
    assert "ArchitecturalScene valide, mais la projection vers le moteur M0 est bloquée. Consultez les raisons affichées." not in source
