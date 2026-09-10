from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_AUDIT = ROOT / "frontend" / "scene-handoff-ownership-audit-v47.js"
SOURCE_LOCK = ROOT / "frontend" / "scene-handoff-source-lock.js"


def test_uncertain_ownership_does_not_erase_certain_target_linked_assembly():
    text = OWNERSHIP_AUDIT.read_text(encoding="utf-8")

    assert 'subject_ownership="external_context" with certainty="certain": NEVER create' in text
    assert "do not let that uncertain attribute erase an observation whose object existence is certain" in text
    assert "certain relation chain anchored to the target building" in text
    assert "keep the ownership uncertainty explicit" in text
    assert "does not assert target ownership" in text
    assert "Never use this rule for an observation whose ownership is certainly external_context" in text

    # BH-232 removes the previous blanket rule that treated any uncertain ownership
    # as permission to delete an otherwise certain, target-linked exterior object.
    assert "If the matching Survey observation is certain external context or has unresolved/uncertain ownership, remove" not in text


def test_scene_source_lock_carries_ownership_value_and_relation_evidence():
    text = SOURCE_LOCK.read_text(encoding="utf-8")

    # Generic fixture shape exercised by this contract:
    # building_boundary <-certain connects_to- platform <-certain connects_to- stair
    # while platform/stair subject_ownership remains plausible. The generated
    # handoff must expose both the ownership VALUE and the certain relation graph,
    # so a neutral Scene reconstruction can preserve existence without promotion.
    assert "'subject_ownership'" in text
    assert "certainty: item.certainty" in text
    assert "subject_id: item.subject_id" in text
    assert "object_id: item.object_id" in text
    assert "Une ownership plausible/unproven n'est jamais promue" in text
    assert "elle ne suffit pas à effacer un objet certain relié par des relations Survey certaines" in text


def test_bh232_policy_is_generic_not_benchmark_specific():
    for path in (OWNERSHIP_AUDIT, SOURCE_LOCK):
        assert "real-house-5" not in path.read_text(encoding="utf-8")
