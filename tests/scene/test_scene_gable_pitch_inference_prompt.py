from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_prompt_infers_pitch_only_from_visible_scaled_gable_geometry() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "PENTE DE TOIT INFÉRÉE DEPUIS UN PIGNON VISIBLE" in source
    assert "les deux égouts et le faîtage/sommet" in source
    assert "rise/run" in source
    assert 'source.kind="inferred"' in source
    assert "confiance prudente" in source
    assert "AUCUN angle par défaut" in source
    assert "pitch_degrees:null" in source
    assert "besoin de satisfaire M0" in source
