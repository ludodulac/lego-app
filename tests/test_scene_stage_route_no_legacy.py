from pathlib import Path


def test_scene_stage_never_reimports_legacy_photo_wizard():
    text = (Path(__file__).resolve().parents[1] / "frontend" / "scene.html").read_text(encoding="utf-8")
    forbidden = ("photo.html", "download-ai-package", "Créer le PDF unique à envoyer à l’IA")
    for token in forbidden:
        assert token not in text
