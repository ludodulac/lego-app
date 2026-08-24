from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-prompt.txt"


def test_survey_v28_prompt_locks_backend_shapes() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "RELEVÉ ARCHITECTURAL v2.8" in source
    assert '"front_facade":"front"' in source
    assert '"x_direction":"front_view_left_to_right"' in source
    assert 'source` est un objet `{ "kind":"user_provided|observed|inferred|generated_default", "confidence":0..1 }`' in source
    assert 'Chaque `evidence[]` est un objet `{ "photo_index":1, "observation":"..." }`' in source
    assert "`representation_policy` est OBLIGATOIREMENT UN OBJET JSON, JAMAIS une liste" in source
    assert '"preserve_nominal_materials":true' in source
    assert "Si c’est une liste, CORRIGE-LA avant de répondre" in source


def test_survey_v28_prompt_locks_enum_like_ai_outputs() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert 'N’écris jamais `semantic_type:"opening"`' in source
    assert 'Si `semantic_type:"opening"` apparaît, SUPPRIME ce champ' in source
    assert "`flat`, `gable`, `hip`, `shed`, `mansard`, `gambrel`, `butterfly`, `other`" in source
    assert "N’invente jamais une valeur composée libre comme `low-slope_or_flat_appearance`" in source
    assert "TOITURE — PRÉFLIGHT MULTI-VUES" in source
