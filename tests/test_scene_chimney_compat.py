from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_certain_chimney_compat_is_loaded_after_scene_normalizer():
    source = (ROOT / "frontend" / "photo.html").read_text()
    scene_index = source.index("scene-handoff-photo-evidence.js")
    chimney_index = source.index("scene-chimney-compat.js")
    import_index = source.index("photo.js")
    assert scene_index < chimney_index < import_index


def test_certain_chimney_recovery_is_exact_id_and_survey_guarded():
    source = (ROOT / "frontend" / "scene-chimney-compat.js").read_text()
    assert "item?.kind === 'chimney'" in source
    assert "item?.certainty === 'certain'" in source
    assert "certainChimneyIds.has(volume?.id)" in source
    assert "positivePropertyValueNumber(volume.width)" in source
    assert "positivePropertyValueNumber(volume.depth)" in source
    assert "positivePropertyValueNumber(volume.height)" in source
    assert "clone.chimneys.push" in source
    assert "clone.volumes = retainedVolumes" in source
    assert "volume_main" not in source
