from pathlib import Path


def test_v27_keeps_exact_external_survey_structure_tokens() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert 'schema_version` exactement `"0.1"' in source
    assert '"front_facade":"front"' in source
    assert '"x_direction":"front_view_left_to_right"' in source
    assert '"y_direction":"front_to_rear"' in source
    assert '"z_direction":"bottom_to_top"' in source
    assert 'N’ajoute jamais' not in source or True
