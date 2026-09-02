from pathlib import Path


AUDIT = Path("frontend/brickhouse-survey-final-contract-audit-v32.txt")
PACKAGE = Path("frontend/brickhouse-survey-package-v08.js")


def test_final_contract_audit_closes_observation_kind_vocabulary():
    text = AUDIT.read_text(encoding="utf-8")
    allowed = (
        "`building_boundary`, `terrain`, `material`, `weathering`, `opening`, "
        "`roof`, `chimney`, `equipment`, `volume`, `platform`, `stair`, "
        "`occlusion`, `context`"
    )
    assert allowed in text
    assert '`secondary_volume`' in text
    assert 'utilise `kind:"volume"`' in text
    assert "aucun sous-type libre" in text


def test_final_contract_audit_closes_opening_identity_and_vocabulary():
    text = AUDIT.read_text(encoding="utf-8")
    assert 'kind:"opening"' in text
    assert 'attributes.physical_object_count:1' in text
    assert "EXACTEMENT UNE ouverture physique" in text
    assert "window_or_door" in text
    assert "glazed_or_glazed_opening" in text
    assert "omets `semantic_type`" in text


def test_final_contract_audit_closes_visible_chimney_inventory_and_root_id():
    text = AUDIT.read_text(encoding="utf-8")
    assert 'kind:"chimney"' in text
    assert "photos[].description" in text
    assert "ne contient pas `survey_id`" in text
    assert "les contrôles v3.1 restent satisfaits" in text


def test_v08_package_appends_final_contract_audit_after_v07():
    text = PACKAGE.read_text(encoding="utf-8")
    assert "brickhouse-survey-package-v07.js" in text
    assert "brickhouse-survey-final-contract-audit-v32.txt" in text
    assert "finalContractAwareSurveyFetch" in text
