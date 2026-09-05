from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "frontend" / "scene.html"


def test_scene_route_is_standalone_and_has_one_scene_action():
    text = SCENE.read_text(encoding="utf-8")
    assert "fetch('./photo.html'" not in text
    assert "document.write" not in text
    assert text.count('id="download-scene-handoff"') == 1
    assert "Créer le PDF unique Survey → Scene" in text
    assert 'id="download-ai-package"' not in text
    assert "Créer le PDF unique à envoyer à l’IA" not in text


def test_scene_route_contains_real_generator_contract_and_benchmark_inputs():
    text = SCENE.read_text(encoding="utf-8")
    for slot in ("front", "right", "left", "rear"):
        assert f'data-slot="{slot}"' in text
    assert "brickhouse-survey-package.js?v=scene-stage-bh146-standalone" in text
    assert "scene-handoff-photo-evidence.js?v=scene-stage-bh146-standalone" in text
    assert "scene-stage-ui.js?v=scene-stage-ui-bh146-standalone" in text
    assert 'id="scene-handoff-home"' in text
    assert 'id="external-analysis"' in text
    assert 'id="import-analysis"' in text


def test_scene_route_user_copy_forbids_stage_regression():
    text = SCENE.read_text(encoding="utf-8")
    assert "Le relevé validé est déjà figé" in text
    assert "aucun nouveau Survey à produire" in text
    assert "Il n’y a rien à réimporter" in text
