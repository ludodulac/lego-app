from pathlib import Path


def test_v27_keeps_supports_inside_platform_attributes() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Les poteaux sous une plateforme vont dans `attributes.supports`" in source
