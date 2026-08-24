from pathlib import Path


PROMPT = Path("frontend/brickhouse-survey-to-scene-prompt.txt")


def _text() -> str:
    return PROMPT.read_text(encoding="utf-8")


def test_scene_prompt_preserves_explicit_plausible_roof_type_without_promoting_certainty() -> None:
    text = _text()

    assert "SURVEY → SCENE v3.8" in text
    assert "attributes.roof_type" in text
    assert "attribute_certainty:\"plausible\"" in text
    assert "source.kind=\"inferred\"" in text
    assert "ne la transforme jamais en fait certain" in text
    assert "attribute_certainty:\"unproven\"" in text
    assert "utilise alors `type:\"other\"`" in text


def test_plausible_gable_may_keep_null_metrics_but_visible_geometry_can_support_inferred_pitch() -> None:
    text = _text()

    assert "Si `gable` est établi ou explicitement plausible" in text
    assert "`ridge_direction:null` et/ou `pitch_degrees:null`" in text
    assert "Un `gable` certain ou explicitement plausible" in text
    assert "pente numérique est TOUJOURS `source.kind=\"inferred\"`" in text
    assert "ne rehausse jamais la certitude de forme" in text
    assert "Conserve `pitch_degrees:null`" in text
