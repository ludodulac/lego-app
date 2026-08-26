from pathlib import Path


def test_scene_required_inputs_ui_explains_bounded_roof_pitch_without_guessing() -> None:
    source = Path("frontend/scene-required-inputs.js").read_text(encoding="utf-8")
    assert "shed_construction_requires_exact_pitch" in source
    assert "Il manque la pente exacte du toit" in source
    assert "entre ${range.min}° et ${range.max}°" in source
    assert "ne choisira pas un angle à votre place" in source
    assert "(range.min + range.max) / 2" not in source


def test_scene_build_loads_required_inputs_ui() -> None:
    source = Path("frontend/scene-build.js").read_text(encoding="utf-8")
    assert "import './scene-required-inputs.js';" in source
