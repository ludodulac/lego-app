"""I/O helpers for BuildingModel validation."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BuildingModel


def load_building_model(path: str | Path) -> BuildingModel:
    """Load UTF-8 JSON from disk and validate it as BuildingModel."""
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return BuildingModel.model_validate(payload)
