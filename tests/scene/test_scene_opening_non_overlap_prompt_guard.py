from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_prompt_requires_openings_to_be_physically_non_overlapping() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "NON-CHEVAUCHEMENT DES OUVERTURES" in source
    assert "deux ouvertures distinctes d’une même façade ne doivent jamais se chevaucher" in source
    assert "offset_horizontal + width" in source
    assert "offset_vertical + height" in source
    assert "réduis la précision métrique" in source
    assert "n’invente jamais une fusion" in source


def test_scene_prompt_final_audit_checks_opening_non_overlap() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "aucune paire d’ouvertures distinctes ne se chevauche sur une même façade" in source
