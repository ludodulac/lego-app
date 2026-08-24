from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_external_import_loads_survey_first_pdf_override() -> None:
    importer = (FRONTEND / "external-bundle-import.js").read_text(encoding="utf-8")
    assert "import './brickhouse-survey-package.js';" in importer


def test_initial_pdf_requests_only_architectural_survey() -> None:
    source = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    assert "PDF_HANDOFF_VERSION = 'pdf-handoff-0.3'" in source
    assert "brickhouse-survey-result.json" in source
    assert "produis UNIQUEMENT un ArchitecturalSurvey v0.1 complet" in source
    assert "NE CONSTRUIS PAS DE SCENE dans ce tour" in source
    assert "Aucun wrapper, aucune clé survey, aucune Scene" in source
    assert "brickhouse-survey-to-scene-prompt.txt" not in source


def test_survey_first_pdf_audits_known_external_ai_failures() -> None:
    source = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    assert "id et name sont présents et non vides" in source
    assert "image_left_maps_to_facade_offset vaut exactement" in source
    assert "jamais null" in source
    assert 'semantic_type:\\"opening\\"' in source
    assert "chaque relation référence deux IDs d’observations existantes" in source


def test_survey_first_pdf_keeps_topology_as_intermediate_reasoning() -> None:
    source = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    assert "brickhouse-topology-prompt.txt" in source
    assert "brickhouse-survey-prompt.txt" in source
    assert "TOPOLOGIE — RAISONNEMENT INTERMÉDIAIRE" in source
    assert "ARCHITECTURAL SURVEY — CONTRAT AUTORITATIF" in source
