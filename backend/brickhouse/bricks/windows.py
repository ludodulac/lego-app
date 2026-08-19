"""Validated real LEGO window assemblies for BrickHouse.

Compatibility is explicit: a pane is never paired to a frame by name similarity.
Families below are backed by catalog compatibility, not inferred from dimensions.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, Field
from brickhouse.building.models import BuildingModel, Facade, OpeningType
from .building_layout import BuildingBrickShell

@dataclass(frozen=True)
class WindowAssemblyDefinition:
    id:str; frame_part_id:str; pane_part_id:str; width_studs:int; height_bricks:int

VALIDATED_WINDOW_ASSEMBLIES:tuple[WindowAssemblyDefinition,...]=(
    WindowAssemblyDefinition("window-1x2x2-60592-60601","WINDOW_1X2X2_60592","GLASS_FOR_WINDOW_1X2X2_60601",2,2),
    WindowAssemblyDefinition("window-1x2x3-60593-60602","WINDOW_1X2X3_60593","GLASS_FOR_WINDOW_1X2X3_60602",2,3),
    WindowAssemblyDefinition("window-1x4x3-60594-60603","WINDOW_1X4X3_60594","GLASS_FOR_WINDOW_1X4X3_60603",4,3),
)

class WindowPartPlacement(BaseModel):
    part_id:str; category:Literal["window_frame","window_pane"]; facade:Facade
    x_studs:int=Field(ge=0); y_studs:int=Field(ge=0); z_plates:int=Field(ge=0)
    rotation_quarter_turns:Literal[0,1,2,3]=0

def _to_global(facade:Facade,local_x:int,opening_width:int,z_bricks:int,width_studs:int,depth_studs:int)->tuple[int,int,int,Literal[0,1,2,3]]:
    """Map facade-local window origin to global studs with correct orientation.

    Window part IDs use LEGO 1xN dimensions: the N axis must run horizontally
    along the facade. Front/rear therefore use a quarter turn; side facades do
    not. Mirrored rear/left origins account for the full opening width.
    """
    z=z_bricks*3
    if facade is Facade.FRONT:return local_x,0,z,1
    if facade is Facade.REAR:return width_studs-local_x-opening_width,depth_studs-1,z,1
    if facade is Facade.RIGHT:return width_studs-1,local_x,z,0
    return 0,depth_studs-local_x-opening_width,z,0

def choose_window_assembly(width_studs:int,height_bricks:int)->WindowAssemblyDefinition|None:
    """Return a validated assembly only for an exact rasterized opening fit."""
    return next((a for a in VALIDATED_WINDOW_ASSEMBLIES if a.width_studs==width_studs and a.height_bricks==height_bricks),None)

def generate_window_assemblies(building:BuildingModel,shell:BuildingBrickShell)->tuple[list[WindowPartPlacement],set[str]]:
    openings={o.id:o for o in building.openings}; walls={w.facade:w for w in shell.walls}
    front=walls[Facade.FRONT].grid.width_studs; depth=walls[Facade.RIGHT].grid.width_studs
    placements:list[WindowPartPlacement]=[]; fitted:set[str]=set()
    for facade in (Facade.FRONT,Facade.REAR,Facade.LEFT,Facade.RIGHT):
        for raster in walls[facade].grid.openings:
            opening=openings.get(raster.id)
            if not opening or opening.type is not OpeningType.WINDOW:continue
            assembly=choose_window_assembly(raster.width_studs,raster.height_bricks)
            if assembly is None:continue
            x,y,z,rotation=_to_global(facade,raster.x_studs,raster.width_studs,raster.z_bricks,front,depth)
            placements.extend((
                WindowPartPlacement(part_id=assembly.frame_part_id,category="window_frame",facade=facade,x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=rotation),
                WindowPartPlacement(part_id=assembly.pane_part_id,category="window_pane",facade=facade,x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=rotation),
            )); fitted.add(raster.id)
    return placements,fitted
