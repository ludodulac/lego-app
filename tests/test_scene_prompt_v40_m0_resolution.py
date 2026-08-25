from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_v40_forces_multiview_envelope_audit_before_null() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "PROMPT DE RECONSTRUCTION SURVEY → SCENE v4.0" in source
    assert "ENVELOPPE PRINCIPALE" in source
    assert "VOLUMES SECONDAIRES" in source
    assert "tente obligatoirement une estimation proportionnelle multi-vues" in source
    assert "ne doit pas rester entièrement `width/depth/height:null`" in source
    assert "La prudence doit être cohérente entre objets" in source


def test_scene_v40_resolves_visible_certain_contacts_instead_of_hiding_behind_unresolved() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "RACCORDS VISIBLES" in source
    assert "CHAQUE relation physique certaine (`connects_to` ou `adjacent_to`)" in source
    assert "contact visible" in source
    assert "rejoint visiblement" in source
    assert "arrive contre" in source
    assert "INTERDIT `unresolved`" in source
    assert 'geometry_status:"resolved"' in source
    assert 'semantic_anchor_volume_id:"volume_main"' in source


def test_scene_v40_keeps_no_fabrication_safety_boundary() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "ce préflight n’autorise ni typologie par défaut, ni dimension standard, ni contact caché" in source
    assert "Une connexion cachée inventée pour satisfaire le validateur est interdite" in source
    assert "Ne déplace pas l’extrémité jusqu’à l’objet pour fabriquer le contact" in source
    assert "volume_geometry_incomplete" in source
    assert "gable_geometry_incomplete" in source
