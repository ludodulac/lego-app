from pathlib import Path


def test_scene_preview_loads_platform_structure_status() -> None:
    html = Path("frontend/scene-viewer.html").read_text(encoding="utf-8")
    assert "scene-platform-structure-status.js" in html


def test_platform_structure_status_preserves_non_metric_observation() -> None:
    source = Path("frontend/scene-platform-structure-status.js").read_text(encoding="utf-8")
    assert "platform_structure_observations" in source
    assert "poteaux verticaux visibles" in source
    assert "contreventements diagonaux visibles" in source
    assert "nombre exact inconnu" in source
    assert "positions exactes inconnues" in source
    assert "Aucun support 3D arbitraire n’est ajouté." in source
    assert "BoxGeometry" not in source
    assert "Mesh(" not in source


def test_platform_railing_status_does_not_guess_edges() -> None:
    source = Path("frontend/scene-platform-structure-status.js").read_text(encoding="utf-8")
    assert "platform.edge_treatment === 'open_railing' && !platform.edges" in source
    assert "garde-corps ouvert observé" in source
    assert "côtés et interruptions exacts ne sont pas résolus" in source
    assert "Aucun garde-corps 3D arbitraire n’est ajouté." in source


def test_stair_parapet_status_preserves_unmetered_detail() -> None:
    source = Path("frontend/scene-platform-structure-status.js").read_text(encoding="utf-8")
    assert "stair.left_edge === 'solid_parapet'" in source
    assert "stair.right_edge === 'solid_parapet'" in source
    assert "parapet plein observé" in source
    assert "hauteur, son épaisseur et son profil exacts ne sont pas métrés" in source
    assert "Aucun parapet 3D arbitraire n’est ajouté." in source
