from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_survey_scene_prompt_treats_validated_survey_as_sufficient_input() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "entrée complète, autoritative et SUFFISANTE" in source
    assert "N’AS PAS accès aux photos originales" in source
    assert "N’exige, ne réclame et ne suppose aucun PDF" in source
    assert "missing_required_photo_input" in source
    assert "L’absence des fichiers photo bruts n’est JAMAIS un motif" in source


def test_survey_scene_prompt_forbids_empty_scene_fallback() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "cela n’autorise jamais à retourner une Scene vide" in source
    assert "`volumes` ne peut pas être vide" in source
    assert "aucune dépendance à des photos/PDF/fichiers externes n’a été introduite" in source
    assert "si le Survey décrit un bâtiment, `volumes` n’est pas vide" in source
