from pathlib import Path


def test_backend_readiness_doctrine_keeps_scene_contract_immutable():
    text = Path("docs/BH-165-BACKEND-READINESS.md").read_text(encoding="utf-8")
    assert "does not add fields to ArchitecturalSurvey or ArchitecturalScene" in text
    assert "Unknown spatial geometry is **not** automatically a blocker" in text
