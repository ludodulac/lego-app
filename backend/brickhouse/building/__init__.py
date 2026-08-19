"""Building domain models and validation helpers."""

from .models import (
    Appearance,
    AppearanceSection,
    BuildingModel,
    Facade,
    Metadata,
    Opening,
    OpeningType,
    Position3D,
    RidgeDirection,
    Roof,
    RoofType,
    SourceInfo,
    SourceKind,
    Volume,
    VolumeShape,
)
from .validation import load_building_model

__all__ = [
    "Appearance",
    "AppearanceSection",
    "BuildingModel",
    "Facade",
    "Metadata",
    "Opening",
    "OpeningType",
    "Position3D",
    "RidgeDirection",
    "Roof",
    "RoofType",
    "SourceInfo",
    "SourceKind",
    "Volume",
    "VolumeShape",
    "load_building_model",
]
