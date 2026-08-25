from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_prompt_preserves_facade_gable_hypothesis_without_inventing_metrics() -> None:
    source = PROMPT.read_text(encoding="utf-8")

    assert "facade_is_gable" in source
    assert 'facade_is_gable:true' in source
    assert 'type:"gable"' in source
    assert "sans inventer" in source
    assert "ridge_direction:null" in source
    assert "pitch_degrees:null" in source
