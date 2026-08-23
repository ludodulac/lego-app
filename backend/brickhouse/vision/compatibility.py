"""Compatibility checks between photo-derived BuildingModel and the current M0 LEGO engine."""
from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, OpeningType, RoofType, WindowStyle


class M0Compatibility(BaseModel):
    buildable: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def assess_m0_compatibility(building: BuildingModel) -> M0Compatibility:
    """Describe whether the deterministic M0 engine can build this proposal."""
    blockers: list[str] = []
    warnings: list[str] = []

    if len(building.volumes) > 1:
        warnings.append(
            "Les volumes rectangulaires multiples sont construits sur une grille commune ; "
            "les jonctions entre volumes ne sont pas encore optimisées comme une seule maçonnerie continue."
        )

    flat_roofs = [roof for roof in building.roofs if roof.type == RoofType.FLAT]
    if flat_roofs:
        warnings.append(
            "Les volumes à toiture plate sont construits avec leurs murs, mais leur couverture "
            "horizontale LEGO dédiée n'est pas encore générée."
        )

    if any(opening.type == OpeningType.GARAGE_DOOR for opening in building.openings):
        warnings.append(
            "Les portes de garage sont rasterisées comme de grandes ouvertures ; "
            "leur habillage dédié n'est pas encore modélisé."
        )

    windows = [
        opening for opening in building.openings if opening.type == OpeningType.WINDOW
    ]
    if windows:
        warnings.append(
            "BrickHouse préfère un vrai assemblage LEGO cadre + vitrage lorsqu'une baie correspond "
            "exactement à une famille validée. Pour une fenêtre simple ou verticale sans cadre exact, "
            "le moteur peut utiliser un remplissage transparent en briques 1x1 sans inventer de "
            "meneau ou traverse architecturale."
        )

    if any(opening.window_style == WindowStyle.BAY for opening in windows):
        warnings.append(
            "Les bow-windows sont encore représentés par un détail de façade conservateur, "
            "sans avancée volumétrique complète."
        )
    if any(opening.window_style == WindowStyle.FOUR_PANE for opening in windows):
        warnings.append(
            "Les fenêtres four_pane n’ont pas encore de famille de vitrage LEGO validée dédiée dans M0."
        )

    return M0Compatibility(
        buildable=not blockers,
        blockers=blockers,
        warnings=warnings,
    )
