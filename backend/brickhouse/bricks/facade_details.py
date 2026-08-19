"""Deterministic facade-detail placements built from supported standard bricks."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from brickhouse.building.models import BuildingModel, Facade, OpeningType, WindowStyle
from .building_layout import BuildingBrickShell

class FacadeDetailPlacement(BaseModel):
    part_id: str
    category: Literal["facade_detail"] = "facade_detail"
    facade: Facade
    x_studs: int = Field(ge=0); y_studs: int = Field(ge=0); z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0,1,2,3] = 0

def _to_global(facade: Facade, local_x: int, course: int, width_studs: int, depth_studs: int)->tuple[int,int,int]:
    z=course*3
    if facade is Facade.FRONT:return local_x,0,z
    if facade is Facade.REAR:return width_studs-local_x-1,depth_studs-1,z
    if facade is Facade.RIGHT:return width_studs-1,local_x,z
    return 0,depth_studs-local_x-1,z

def _add_cell(cells: dict[tuple[int,int],str], x:int, z:int, part_id:str="BRICK_1X1")->None:
    cells[(x,z)] = part_id

def generate_window_surrounds(building: BuildingModel, shell: BuildingBrickShell)->list[FacadeDetailPlacement]:
    """Create style-aware, catalog-backed masonry details inside window openings.

    M0 deliberately uses only canonical standard bricks here. Styles therefore
    change the *constructible masonry language* (sill, mullion, transom, paired
    divider) without pretending that an unvalidated frame/glass pair exists.
    """
    openings={opening.id:opening for opening in building.openings}
    walls={wall.facade:wall for wall in shell.walls}; front=walls[Facade.FRONT].grid.width_studs; depth=walls[Facade.RIGHT].grid.width_studs
    placements=[]
    for facade in (Facade.FRONT,Facade.REAR,Facade.LEFT,Facade.RIGHT):
        wall=walls[facade]
        for raster in wall.grid.openings:
            opening=openings.get(raster.id)
            if not opening or opening.type is not OpeningType.WINDOW or raster.width_studs<3 or raster.height_bricks<3:continue
            x0=raster.x_studs; x1=x0+raster.width_studs-1; z0=raster.z_bricks; z1=z0+raster.height_bricks-1
            style=opening.window_style or WindowStyle.SIMPLE; cells:dict[tuple[int,int],str]={}
            # Structural jambs and lintel are always present.
            for course in range(z0,z1+1): _add_cell(cells,x0,course); _add_cell(cells,x1,course)
            for x in range(x0+1,x1): _add_cell(cells,x,z1)
            # A sill is explicit metadata, and traditional/bay styles default to one.
            if opening.has_sill or style in {WindowStyle.TRADITIONAL_TALL,WindowStyle.BAY}:
                for x in range(x0+1,x1): _add_cell(cells,x,z0)
            # Four-pane windows get a real central mullion and transom made of bricks.
            if style is WindowStyle.FOUR_PANE:
                mid_x=(x0+x1)//2; mid_z=(z0+z1)//2
                for z in range(z0+1,z1): _add_cell(cells,mid_x,z)
                for x in range(x0+1,x1): _add_cell(cells,x,mid_z)
            # Paired windows are represented by a stronger central divider.
            if style is WindowStyle.PAIRED:
                mid_x=(x0+x1)//2
                for z in range(z0,z1+1): _add_cell(cells,mid_x,z)
            # Traditional tall windows receive a transom in their upper third.
            if style is WindowStyle.TRADITIONAL_TALL:
                transom=max(z0+1,z1-1)
                for x in range(x0+1,x1): _add_cell(cells,x,transom)
            # Bay remains flush in M0 until projecting connection geometry is validated;
            # a sill + centre divider makes the requested style visible without faking it.
            if style is WindowStyle.BAY:
                mid_x=(x0+x1)//2
                for z in range(z0+1,z1): _add_cell(cells,mid_x,z)
            for (local_x,course),part_id in sorted(cells.items(),key=lambda item:(item[0][1],item[0][0])):
                x,y,z=_to_global(facade,local_x,course,front,depth)
                placements.append(FacadeDetailPlacement(part_id=part_id,facade=facade,x_studs=x,y_studs=y,z_plates=z))
    return placements
