"""Bill of materials generation from the canonical BrickModel."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field

from .brick_model import BrickModel, PartCategory


class BOMLine(BaseModel):
    part_id: str
    category: PartCategory
    semantic_color: str | None = Field(default=None, min_length=1)
    quantity: int = Field(gt=0)


class BillOfMaterials(BaseModel):
    schema_version: str = "0.1"
    building_id: str
    volume_id: str
    total_parts: int = Field(gt=0)
    unique_part_types: int = Field(gt=0)
    lines: list[BOMLine] = Field(min_length=1)


def generate_bom(model: BrickModel) -> BillOfMaterials:
    """Aggregate placements without discarding evidence-backed semantic color.

    ``semantic_color`` deliberately remains an architectural descriptor. It is
    not a LEGO catalogue color ID and therefore makes the canonical BOM more
    precise without asserting physical part/color availability.
    """
    counts = Counter((part.part_id, part.category, part.semantic_color) for part in model.parts)
    lines = [
        BOMLine(
            part_id=part_id,
            category=category,
            semantic_color=semantic_color,
            quantity=quantity,
        )
        for (part_id, category, semantic_color), quantity in sorted(
            counts.items(),
            key=lambda item: (item[0][1], item[0][0], item[0][2] or ""),
        )
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
