"""Support-aware gable roof using real piece-family IDs from the project catalog."""
from __future__ import annotations
from math import hypot
from typing import Literal
from pydantic import BaseModel, Field
from brickhouse.building.models import RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, RoofPlaneGeometry
from .building_layout import BuildingBrickShell

COURSE_RISE_PLATES=3

class RoofPartDefinition(BaseModel):
    id:str; category:Literal["roof_tile","ridge_tile"]; width_studs:int=Field(gt=0); length_studs:int=Field(gt=0); height_plates:int=Field(default=1,gt=0); connection_overlap_studs:int=Field(default=0,ge=0)
class RoofPartCatalog(BaseModel):
    schema_version:Literal["0.4"]="0.4"; parts:list[RoofPartDefinition]
    def get(self,part_id:str)->RoofPartDefinition:
        for p in self.parts:
            if p.id==part_id:return p
        raise KeyError(part_id)
def create_m0_roof_catalog()->RoofPartCatalog:
    return RoofPartCatalog(parts=[
        *[RoofPartDefinition(id=f"BRICK_SLOPED_45_2X{s}",category="roof_tile",width_studs=2,length_studs=s,height_plates=3,connection_overlap_studs=1) for s in (1,2,3,4)],
        RoofPartDefinition(id="TILE_2X2",category="ridge_tile",width_studs=2,length_studs=2,height_plates=1,connection_overlap_studs=1),
        RoofPartDefinition(id="TILE_2X3",category="ridge_tile",width_studs=2,length_studs=3,height_plates=1,connection_overlap_studs=1),
        RoofPartDefinition(id="TILE_2X4",category="ridge_tile",width_studs=2,length_studs=4,height_plates=1,connection_overlap_studs=1),
    ])
class GlobalRoofPlacement(BaseModel):
    part_id:str; side:Literal["negative","positive","ridge"]; x_studs:int; y_studs:int; z_plates:int=Field(ge=0); rotation_quarter_turns:Literal[0,1,2,3]
class SpatialRoof(BaseModel):
    schema_version:Literal["0.4"]="0.4"; building_id:str; roof_id:str; ridge_direction:RidgeDirection; placements:list[GlobalRoofPlacement]

def _tile_line(length:int,kind:str)->list[tuple[str,int,int]]:
    choices=((4,"BRICK_SLOPED_45_2X4"),(3,"BRICK_SLOPED_45_2X3"),(2,"BRICK_SLOPED_45_2X2"),(1,"BRICK_SLOPED_45_2X1")) if kind=="slope" else ((4,"TILE_2X4"),(3,"TILE_2X3"),(2,"TILE_2X2"))
    out=[];cursor=0
    for span,pid in choices:
        while cursor+span<=length:out.append((pid,cursor,span));cursor+=span
    if cursor!=length:raise ValueError(f"M0 ridge cannot tile line length {length} with current 2-stud ridge family")
    return out

def _plane_run_and_rise(p:RoofPlaneGeometry)->tuple[float,float]:
    lo=min(x.z for x in p.corners);hi=max(x.z for x in p.corners);e=[x for x in p.corners if abs(x.z-lo)<1e-9];r=[x for x in p.corners if abs(x.z-hi)<1e-9]
    if hi<=lo or not e or not r:raise ValueError("invalid gable roof plane")
    run=hypot(e[0].x-r[0].x,e[0].y-r[0].y)
    if run<=0:raise ValueError("gable roof plane must have positive horizontal run")
    return run,hi-lo
def _gable_planes(g:BuildingGeometry,volume_id:str)->tuple[RoofPlaneGeometry,RoofPlaneGeometry]:
    ps=[p for p in g.roof_planes if p.volume_id==volume_id and p.roof_type is RoofType.GABLE]
    if len(ps)!=2:raise ValueError("BH-025 requires exactly two gable roof planes for the shell volume")
    by={p.side:p for p in ps};a,b=by.get("negative"),by.get("positive")
    if a is None or b is None:raise ValueError("gable roof requires negative and positive planes")
    if a.ridge_direction is None or b.ridge_direction is None or a.ridge_direction is not b.ridge_direction:raise ValueError("gable roof planes must share ridge_direction")
    return a,b
def _footprint(p:GlobalRoofPlacement)->set[tuple[int,int]]:
    d=create_m0_roof_catalog().get(p.part_id);fx,fy=(d.length_studs,d.width_studs) if p.rotation_quarter_turns%2 else (d.width_studs,d.length_studs)
    return {(p.x_studs+dx,p.y_studs+dy) for dx in range(fx) for dy in range(fy)}
def _axis(p:GlobalRoofPlacement,d:RidgeDirection)->int:return p.x_studs if d is RidgeDirection.DEPTH else p.y_studs

def validate_roof_support(roof:SpatialRoof,shell:BuildingBrickShell)->None:
    top=shell.walls[0].grid.height_bricks*3;width=next(r.grid.width_studs for r in shell.walls if r.facade.value=="front");depth=next(r.grid.width_studs for r in shell.walls if r.facade.value=="right")
    for side in ("negative","positive"):
        ps=[p for p in roof.placements if p.side==side];axes=sorted({_axis(p,roof.ridge_direction) for p in ps},reverse=side=="positive")
        if not axes:raise ValueError(f"roof side {side!r} has no slope courses")
        cs=[[p for p in ps if _axis(p,roof.ridge_direction)==a] for a in axes]
        if any(p.z_plates!=top for p in cs[0]):raise ValueError(f"roof side {side!r} eave course is not anchored at wall top")
        first=set().union(*(_footprint(p) for p in cs[0]));edge=0 if side=="negative" else (width-1 if roof.ridge_direction is RidgeDirection.DEPTH else depth-1)
        if not any((x==edge if roof.ridge_direction is RidgeDirection.DEPTH else y==edge) for x,y in first):raise ValueError(f"roof side {side!r} does not contact its eave wall")
        for prev,cur in zip(cs,cs[1:]):
            if not set().union(*(_footprint(p) for p in prev)).intersection(set().union(*(_footprint(p) for p in cur))):raise ValueError(f"floating roof course on side {side!r}")
            if min(p.z_plates for p in cur)-min(p.z_plates for p in prev)!=COURSE_RISE_PLATES:raise ValueError(f"roof side {side!r} does not follow the selected slope connection rise")
    ridge=[p for p in roof.placements if p.side=="ridge"]
    if not ridge:raise ValueError("roof has no ridge")
    rc=set().union(*(_footprint(p) for p in ridge))
    for side in ("negative","positive"):
        ps=[p for p in roof.placements if p.side==side];axes=sorted({_axis(p,roof.ridge_direction) for p in ps},reverse=side=="positive");inner=axes[-1];ic=set().union(*(_footprint(p) for p in ps if _axis(p,roof.ridge_direction)==inner))
        if not rc.intersection(ic):raise ValueError(f"ridge is not connected to roof side {side!r}")

def generate_spatial_gable_roof(g:BuildingGeometry,shell:BuildingBrickShell)->SpatialRoof:
    negative,_=_gable_planes(g,shell.volume_id);_plane_run_and_rise(negative);d=negative.ridge_direction;assert d is not None
    top=shell.walls[0].grid.height_bricks*3;width=next(r.grid.width_studs for r in shell.walls if r.facade.value=="front");depth=next(r.grid.width_studs for r in shell.walls if r.facade.value=="right");span,line=(width,depth) if d is RidgeDirection.DEPTH else (depth,width)
    if span%2:raise ValueError("M0 support-aware gable roof currently requires an even slope span")
    half=span//2;course_count=half-1
    if course_count<1:raise ValueError("roof span is too small for supported slopes and ridge")
    placements=[]
    for side in ("negative","positive"):
        for distance in range(course_count):
            axis=distance if side=="negative" else span-2-distance;z=top+distance*COURSE_RISE_PLATES
            for pid,offset,_ in _tile_line(line,"slope"):
                placements.append(GlobalRoofPlacement(part_id=pid,side=side,x_studs=axis if d is RidgeDirection.DEPTH else offset,y_studs=offset if d is RidgeDirection.DEPTH else axis,z_plates=z,rotation_quarter_turns=0 if d is RidgeDirection.DEPTH else 1))
    ridge_axis=half-1;ridge_z=top+course_count*COURSE_RISE_PLATES
    for pid,offset,_ in _tile_line(line,"ridge"):
        placements.append(GlobalRoofPlacement(part_id=pid,side="ridge",x_studs=ridge_axis if d is RidgeDirection.DEPTH else offset,y_studs=offset if d is RidgeDirection.DEPTH else ridge_axis,z_plates=ridge_z,rotation_quarter_turns=0 if d is RidgeDirection.DEPTH else 1))
    roof=SpatialRoof(building_id=shell.building_id,roof_id=negative.roof_id,ridge_direction=d,placements=placements);validate_roof_support(roof,shell);return roof
