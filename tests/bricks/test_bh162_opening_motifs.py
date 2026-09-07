from brickhouse.bricks.opening_motifs import (
    OPENING_MOTIFS,
    opening_motif_by_id,
    opening_motifs_for_topology,
)
from brickhouse.bricks.windows import VALIDATED_WINDOW_ASSEMBLIES


def test_every_opening_motif_uses_an_existing_validated_window_assembly():
    assemblies = {assembly.id: assembly for assembly in VALIDATED_WINDOW_ASSEMBLIES}
    assert OPENING_MOTIFS
    for motif in OPENING_MOTIFS:
        assembly = assemblies[motif.assembly_id]
        assert motif.frame_part_id == assembly.frame_part_id
        assert motif.pane_part_id == assembly.pane_part_id
        assert motif.depth_studs == 1
        assert motif.connection_strategy == "stud_bearing_in_wall_opening"


def test_unknown_topology_does_not_invent_subdivisions():
    motifs = opening_motifs_for_topology(leaf_count=None, pane_count=None)
    assert motifs
    assert all(motif.composition == "single" for motif in motifs)
    assert all(motif.leaf_count == 1 and motif.pane_count == 1 for motif in motifs)


def test_known_topology_is_a_hard_filter():
    paired = opening_motifs_for_topology(leaf_count=2, pane_count=2)
    assert paired
    assert all(motif.composition == "paired" for motif in paired)

    four_pane = opening_motifs_for_topology(leaf_count=2, pane_count=4)
    assert four_pane
    assert all(motif.composition == "four_pane" for motif in four_pane)

    unsupported = opening_motifs_for_topology(leaf_count=3, pane_count=7)
    assert unsupported == ()


def test_registry_lookup_and_order_are_deterministic():
    ids = [motif.id for motif in OPENING_MOTIFS]
    assert ids == list(dict.fromkeys(ids))
    assert [opening_motif_by_id(motif_id).id for motif_id in ids] == ids
    assert opening_motif_by_id("does-not-exist") is None
