from pathlib import Path


AUDIT = Path("frontend/brickhouse-survey-ownership-audit-v38.txt")
PACKAGE = Path("frontend/brickhouse-survey-package-v13.js")
ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_ownership_audit_requires_explicit_target_context_or_unresolved_classification():
    text = AUDIT.read_text(encoding="utf-8")

    assert "attributes.subject_ownership" in text
    assert '"target_building"' in text
    assert '"external_context"' in text
    assert '"unresolved"' in text
    assert "attribute_certainty.subject_ownership" in text


def test_ownership_audit_rejects_projection_and_adjacency_as_identity_proof():
    text = AUDIT.read_text(encoding="utf-8")

    assert "projection 2D" in text
    assert "proximité" in text
    assert "same_physical_object" in text
    assert "part_of" in text
    assert "ne les fusionne pas" in text or "Ne fusionne pas" in text


def test_ownership_audit_keeps_external_context_out_of_target_scene():
    text = AUDIT.read_text(encoding="utf-8")

    assert "external_context" in text
    assert "ne doit jamais être converti en primitive cible" in text
    assert "cheminées" in text


def test_v13_package_appends_ownership_audit_after_stair_topology_layer_and_is_active():
    package = PACKAGE.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")

    assert "brickhouse-survey-package-v12.js" in package
    assert "brickhouse-survey-ownership-audit-v38.txt" in package
    assert "targetContextAwareSurveyFetch" in package
    assert "brickhouse-survey-package-v13.js" in entry
