from pathlib import Path

import pytest

import brickhouse.pipeline as pipeline
from brickhouse.bricks.piece_capabilities import load_piece_master


REFERENCE = Path("docs/examples/building-model-simple-house.json")
MASTER = Path("data/processed/piece_types_master.csv")


def test_pipeline_rejects_parts_when_registry_has_not_approved_them(monkeypatch):
    known_only = load_piece_master(MASTER)
    monkeypatch.setattr(
        pipeline,
        "create_current_engine_capability_registry",
        lambda: known_only,
    )
    with pytest.raises(ValueError, match="not approved for deterministic placement"):
        pipeline.run_m0_pipeline(REFERENCE, front_width_studs=48)
