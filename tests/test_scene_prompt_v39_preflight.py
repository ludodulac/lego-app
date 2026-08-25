from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_scene_v39_requires_multiview_metric_preflight_before_null_or_unresolved() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "PROMPT DE RECONSTRUCTION SURVEY → SCENE v3.9" in source
    assert "PRÉFLIGHT M0 MULTI-VUES — OBLIGATOIRE AVANT SORTIE" in source
    assert "tente obligatoirement une estimation proportionnelle multi-vues" in source
    assert "le simple fait que les dimensions soient `inferred` n’interdit pas une résolution géométrique cohérente" in source
    assert "préflight M0 multi-vues exécuté avant toute décision `null`/`unresolved`" in source


def test_scene_v39_preserves_certain_exterior_inventory_without_fabrication() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "pour chaque observation Survey active `platform` ou `stair` de certitude `certain`" in source
    assert "une primitive Scene de même ID existe" in source
    assert "Une primitive visible ne peut pas disparaître parce que sa métrique est difficile" in source
    assert "ce préflight n’autorise ni typologie par défaut, ni dimension standard, ni contact caché" in source
    assert "chaque `platform`/`stair` certain du Survey est rendu avec le même ID" in source
