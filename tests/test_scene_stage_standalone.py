from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "frontend" / "scene.html"
RUNTIME = ROOT / "frontend" / "scene-benchmark-runtime.js"


def test_scene_route_is_standalone_and_has_one_scene_action():
    text = SCENE.read_text(encoding="utf-8")
    assert "fetch('./photo.html'" not in text
    assert "document.write" not in text
    assert text.count('id="download-scene-handoff"') == 1
    assert "Créer le PDF Relevé → Scene 3D" in text
    assert 'id="download-ai-package"' not in text
    assert "Créer le PDF unique à envoyer à l’IA" not in text


def test_scene_route_contains_real_generator_contract_and_benchmark_inputs():
    text = SCENE.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    for slot in ("front", "right", "left", "rear"):
        assert f'data-slot="{slot}"' in text
    assert "scene-benchmark-runtime.js?v=bh147-scene-runtime-1" in text
    assert "scene-handoff-photo-evidence.js?v=scene-runtime-bh147" in runtime
    assert "accepted-survey-v0.1.json" in runtime
    assert "valid_for_scene_fusion: true" in runtime
    assert 'id="scene-handoff-home"' in text
    assert 'id="external-analysis"' not in text
    assert 'id="import-analysis"' not in text


def test_scene_route_user_copy_forbids_stage_regression():
    text = SCENE.read_text(encoding="utf-8")
    assert "Le relevé validé est déjà figé" in text
    assert "aucun nouveau relevé à produire" in text
    assert "Il n’y a rien à réimporter" in text
