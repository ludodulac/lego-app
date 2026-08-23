from pathlib import Path

from brickhouse.bricks.piece_capabilities import (
    PieceCapabilityStage,
    create_current_engine_capability_registry,
    load_piece_master,
    promote_capabilities,
)


MASTER = Path("data/processed/piece_types_master.csv")


def test_master_catalogue_is_known_but_not_automatically_placeable():
    registry = load_piece_master(MASTER)
    exotic = registry.get("BRICK_SLOPED_65_2X2X2")
    assert exotic.source_dataset_known is True
    assert exotic.stage is PieceCapabilityStage.KNOWN
    assert exotic.auto_placeable is False


def test_fractional_piece_dimensions_are_preserved_from_source_data():
    registry = load_piece_master(MASTER)
    piece = registry.get("BRICK_SLOPED_30_1X2X2_3")
    assert piece.height_studs == 2 / 3


def test_current_engine_promotes_only_explicitly_supported_families():
    registry = create_current_engine_capability_registry(MASTER)
    assert registry.get("BRICK_1X8").auto_placeable is True
    assert registry.get("BRICK_SLOPED_45_2X4").auto_placeable is True
    assert registry.get("BRICK_SLOPED_65_2X2X2").auto_placeable is False


def test_engine_canonical_alias_can_be_approved_without_faking_source_presence():
    registry = load_piece_master(MASTER)
    promoted = promote_capabilities(
        registry,
        ["ENGINE_ONLY_TEST_PART"],
        stage=PieceCapabilityStage.PLACEMENT_APPROVED,
        notes="test",
    )
    piece = promoted.get("ENGINE_ONLY_TEST_PART")
    assert piece.source_dataset_known is False
    assert piece.auto_placeable is True
