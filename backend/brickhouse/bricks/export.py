"""Stable JSON export bundle for BrickModel downstream consumers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator

from .bom import BillOfMaterials
from .brick_model import BrickModel


class BrickExportMetadata(BaseModel):
    generator: Literal["brickhouse-engine"] = "brickhouse-engine"
    coordinate_system: Literal["stud-grid"] = "stud-grid"
    vertical_unit: Literal["plate"] = "plate"


class BrickExportBundle(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    metadata: BrickExportMetadata = BrickExportMetadata()
    brick_model: BrickModel
    bom: BillOfMaterials

    @model_validator(mode="after")
    def validate_consistency(self) -> "BrickExportBundle":
        if self.brick_model.building_id != self.building_id:
            raise ValueError("BrickModel building_id does not match export building_id")
        if self.bom.building_id != self.building_id:
            raise ValueError("BOM building_id does not match export building_id")
        if self.brick_model.volume_id != self.volume_id:
            raise ValueError("BrickModel volume_id does not match export volume_id")
        if self.bom.volume_id != self.volume_id:
            raise ValueError("BOM volume_id does not match export volume_id")
        if self.bom.total_parts != len(self.brick_model.parts):
            raise ValueError("BOM total_parts does not match BrickModel part count")
        return self


def create_export_bundle(model: BrickModel, bom: BillOfMaterials) -> BrickExportBundle:
    """Create the viewer/export bundle from one BrickModel and its BOM."""
    return BrickExportBundle(
        building_id=model.building_id,
        volume_id=model.volume_id,
        brick_model=model,
        bom=bom,
    )


def export_bundle_json(bundle: BrickExportBundle, *, indent: int = 2) -> str:
    """Serialize an export bundle as deterministic UTF-8 JSON text."""
    return bundle.model_dump_json(indent=indent, exclude_none=True)
