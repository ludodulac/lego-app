"""Bill of materials generation from the canonical BrickModel."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field

from .brick_model import BrickModel


class BOMLine(BaseModel):
    part_id: str
    category: Literal["brick", "roof_tile", "ridge_tile"]
    quantity: int = Field(gt=0)


class BillOfMaterials(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    total_parts: int = Field(gt=0)
    unique_part_types: int = Field(gt=0)
    lines: list[BOMLine] = Field(min_length=1)


def generate_bom(model: BrickModel) -> BillOfMaterials:
    """Aggregate BrickModel placements by canonical part id and category."""
    counts = Counter((part.part_id, part.category) for part in model.parts)
    lines = [
        BOMLine(part_id=part_id, category=category, quantity=quantity)
        for (part_id, category), quantity in sorted(counts.items(), key=lambda item: (item[0][1], item[0][0]))
    ]
    total = sum(line.quantity for line in lines)
    if total != len(model.parts):
        raise RuntimeError("BOM quantity total does not match BrickModel part count")

    return BillOfMaterials(
        building_id=model.building_id,
        volume_id=model.volume_id,
        total_parts=total,
        unique_part_types=len(lines),
        lines=lines,
    )
