from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_prompt_requires_structured_support_posts() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "SupportPost :" in source
    assert '"position":{"x":0.0,"y":0.0,"z":0.0}' in source
    assert '"width":0.15' in source
    assert '"depth":0.15' in source
    assert '"height":2.4' in source
    assert "Platform.supports` est TOUJOURS une liste d’objets SupportPost complets" in source
    assert "N’écris jamais une chaîne" in source
