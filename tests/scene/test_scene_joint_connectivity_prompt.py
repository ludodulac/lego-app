from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_prompt_requires_joint_resolution_of_visible_multiview_contacts():
    source = PROMPT.read_text(encoding="utf-8")
    assert "SURVEY → SCENE v3.7" in source
    assert "RÉSOLUTION MÉTRIQUE CONJOINTE DES RACCORDS MULTI-VUES" in source
    assert "escalier→plateforme" in source
    assert "plateforme→plateforme" in source
    assert "plateforme→bâtiment" in source
    assert "tolérance backend 0,12 m" in source
    assert "estimations indépendantes créent un petit vide" in source
    assert "N’AUTORISE JAMAIS à créer un contact caché" in source


def test_prompt_maps_resolved_semantic_boundary_without_renaming_survey_endpoint():
    source = PROMPT.read_text(encoding="utf-8")
    assert "semantic_anchor_volume_id" in source
    assert "Ne renomme jamais `building_boundary` en `volume_main`" in source
    assert 'geometry_status:"resolved" + `semantic_anchor_volume_id`' in source
    assert "si la primitive touche réellement un volume Scene non ambigu" in source
