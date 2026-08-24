from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "frontend" / "brickhouse-survey-to-scene-prompt.txt"


def test_multiview_prompt_allows_prudent_envelope_inference_from_known_scale() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "ENVELOPPE MÉTRIQUE MULTI-VUES" in source
    assert "Une largeur utilisateur peut servir d’ancre d’échelle" in source
    assert "plusieurs vues cohérentes contraignent réellement profondeur ou hauteur" in source
    assert 'source.kind="inferred"' in source
    assert "confiance prudente" in source
    assert "value:null" in source
    assert "réellement non contrainte" in source


def test_multiview_prompt_does_not_promote_inference_to_measurement() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "ne devient jamais user_provided" in source
    assert "N’invente pas une profondeur ou hauteur uniquement pour satisfaire M0" in source
