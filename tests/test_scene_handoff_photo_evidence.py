from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_staged_scene_handoff_requires_original_photo_pdf() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "scene-handoff-0.3-photo-evidence" in source
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in source
    assert "ENTRÉES OBLIGATOIRES — DEUX FICHIERS" in source
    assert "INTERDICTION DE PROJECTION SANS IMAGES" in source
    assert "Ne tente pas de reconstruire la Scene depuis le Survey textuel seul" in source
    assert "Ignore dans ce PDF toute ancienne instruction demandant de produire un Survey" in source


def test_staged_scene_handoff_locks_exact_scene_serialization_shapes() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "CONTRAT DE SÉRIALISATION — OBLIGATOIRE" in source
    assert 'Chaque evidence Scene est un OBJET exactement de la forme' in source
    assert 'N’écris jamais une chaîne comme \\"photo:1\\"' in source
    assert "SceneVolume.floors est un ENTIER" in source
    assert "Platform utilise thickness, jamais height" in source
    assert "appearance est toujours présent" in source


def test_external_scene_import_has_conservative_shape_normalizer() -> None:
    source = (FRONTEND / "scene-handoff-photo-evidence.js").read_text(encoding="utf-8")
    assert "function normalizeEvidenceList" in source
    assert "function normalizeExternalScene" in source
    assert "^photo:(\\d+)$" in source
    assert "volume.floors.value" in source
    assert "platform.thickness = Number(platform.height)" in source
    assert "clone.appearance = {}" in source
    assert "normalizeSceneTextareaBeforeImport" in source


def test_photo_page_loads_photo_backed_scene_handoff_guard() -> None:
    source = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert "scene-handoff-photo-evidence.js?v=scene-handoff-0.2" in source
