"""Compatibility checks between photo-derived BuildingModel and the current M0 LEGO engine."""
from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, RoofType


class M0Compatibility(BaseModel):
    buildable: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def assess_m0_compatibility(building: BuildingModel) -> M0Compatibility:
    """Describe whether the current deterministic M0 engine can build this proposal.

    This is intentionally conservative. Unsupported geometry must be made visible
    to the user instead of being silently simplified into a different house.
    """
    blockers: list[str] = []
    warnings: list[str] = []

    if len(building.volumes) != 1:
        blockers.append("Le moteur photo M0 construit encore un seul volume principal rectangulaire.")

    if len(building.roofs) != 1:
        blockers.append("Le moteur M0 exige exactement une toiture sur le volume principal.")
    elif building.roofs[0].type is not RoofType.GABLE:
        blockers.append("Le moteur M0 construit actuellement uniquement les toits à deux pans.")

    if any(opening.type.value == "garage_door" for opening in building.openings):
        warnings.append("Les portes de garage sont rasterisées comme de grandes ouvertures ; leur habillage dédié n'est pas encore modélisé.")

    if any(opening.window_style and opening.window_style.value == "bay" for opening in building.openings):
        warnings.append("Les bow-windows sont encore représentés par un détail de façade conservateur, sans avancée volumétrique complète.")

    return M0Compatibility(buildable=not blockers, blockers=blockers, warnings=warnings)
