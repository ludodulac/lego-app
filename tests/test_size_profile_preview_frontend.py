from pathlib import Path


def test_configurator_exposes_physical_profile_preview_without_hiding_raw_engine_sizes():
    html = Path("frontend/configurator.html").read_text(encoding="utf-8")
    source = Path("frontend/size-profile.js").read_text(encoding="utf-8")

    assert "Compact — facile à exposer" in html
    assert "Standard — recommandé" in html
    assert "Grand — plus de détails" in html
    assert '<script type="module" src="./size-profile.js"></script>' in html
    assert "const physicalWidthCm=frontStuds*.8" in source
    assert "Math.round(frontStuds*realDepthM/realWidthM)" in source
    assert "const scaleDenominator=realWidthM/(frontStuds*.008)" in source
    assert "Le nombre de pièces est calculé par le moteur" in source
