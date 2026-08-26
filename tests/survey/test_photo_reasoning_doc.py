from pathlib import Path


def test_photo_reasoning_loop_keeps_questions_between_observation_and_geometry() -> None:
    text = Path("docs/PHOTO_REASONING_LOOP.md").read_text(encoding="utf-8")
    assert "Observe one photo at a time" in text
    assert "Keep hypotheses separate from facts" in text
    assert "Map only sufficiently supported facts to simple architectural primitives" in text
    assert "Prefer information gain over generic questioning" in text
    assert "Convert only validated geometry to LEGO" in text
