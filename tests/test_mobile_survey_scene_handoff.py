from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURVEY_IMPORT = ROOT / "frontend" / "survey-import.js"


def test_validated_survey_offers_one_file_scene_handoff() -> None:
    source = SURVEY_IMPORT.read_text(encoding="utf-8")
    assert "SCENE_HANDOFF_VERSION = 'scene-handoff-0.1'" in source
    assert "SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE.txt'" in source
    assert "Créer le fichier Survey → Scene à envoyer à l’IA" in source
    assert "Sur téléphone, vous n’avez rien à copier" in source
    assert "brickhouse-survey-to-scene-prompt.txt" in source


def test_scene_handoff_embeds_validated_survey_and_user_width() -> None:
    source = SURVEY_IMPORT.read_text(encoding="utf-8")
    assert "const enriched = withKnownWidth(currentValidatedSurvey)" in source
    assert "ARCHITECTURAL SURVEY VALIDÉ" in source
    assert "JSON.stringify(enriched, null, 2)" in source
    assert "largeur avant ${width.value} m incluse" in source


def test_scene_handoff_requests_scene_root_file_only() -> None:
    source = SURVEY_IMPORT.read_text(encoding="utf-8")
    assert "brickhouse-scene-result.json" in source
    assert "UNIQUEMENT un objet ArchitecturalScene v0.2 complet à la racine" in source
    assert "ne mets pas la Scene dans une clé" in source
    assert 'geometry_status:\\"unresolved\\"' in source
