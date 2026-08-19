"""Support-aware canonical gable roof generation."""
from __future__ import annotations
from math import floor, hypot
from typing import Literal
from pydantic import BaseModel, Field
from brickhouse.building.models import RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, RoofPlaneGeometry
from .building_layout import BuildingBrickShell

class RoofPartDefinition(BaseModel):
    id: str
    category: Literal["roof_tile","ridge_tile"]
    width_studs: int = Field(gt=0)
    length_studs: int = Field(gt=0)
    height_plates: int = Field(default=1,gt=0)
    connection_overlap_studs: int = Field(default=0,ge=0)

class RoofPartCatalog(BaseModel):
    schema_version: Literal["0.2"]="0.2"
    parts: list[RoofPartDefinition]
    def get(self,part_id:str)->RoofPartDefinition:
        for part in self.parts:
            if part.id==part_id:return part
        raise KeyError(part_id)

def create_m0_roof_catalog()->RoofPartCatalog:
    spans=(1,2,4,6,8)
    return RoofPartCatalog(parts=[
        *[RoofPartDefinition(id=f"ROOF_SLOPE_2X{s}",category="roof_tile",width_studs=2,length_studs=s,connection_overlap_studs=1) for s in spans],
        *[RoofPartDefinition(id=f"RIDGE_TILE_1X{s}",category="ridge_tile",width_studs=1,length_studs=s,connection_overlap_studs=1) for s in spans],
    ])

class GlobalRoofPlacement(BaseModel):
    part_id:str
    side:Literal["negative","positive","ridge"]
    x_studs:int
    y_studs:int
    z_plates:int=Field(ge=0)
    rotation_quarter_turns:Literal[0,1,2,3]

class SpatialRoof(BaseModel):
    schema_version:Literal["0.2"]="0.2"
    building_id:str
    roof_id:str
    ridge_direction:RidgeDirection
    placements:list[GlobalRoofPlacement]

def _round(value:float)->int:return floor(value+.5)

def _tile_line(length:int,prefix:str)->list[tuple[str,int,int]]:
    spans=(8,6,4,2,1); result=[]; cursor=0
    for span in spans:
        pid=f"ROOF_SLOPE_2X{span}" if prefix=="ROOF_SLOPE" else f"RIDGE_TILE_1X{span}"
        while cursor+span<=length:
            result.append((pid,cursor,span));cursor+=span
    if cursor!=length:raise RuntimeError(f"could not tile roof line of length {length}")
    return result

def _plane_run_and_rise(plane:RoofPlaneGeometry)->tuple[float,float]:
    lo=min(p.z for p in plane.corners); hi=max(p.z for p in plane.corners); rise=hi-lo
    e=[p for p in plane.corners if abs(p.z-lo)<1e-9]; r=[p for p in plane.corners if abs(p.z-hi)<1e-9]
    if rise<=0 or not e or not r:raise ValueError("invalid gable roof plane")
    run=hypot(e[0].x-r[0].x,e[0].y-r[0].y)
    if run<=0:raise ValueError("gable roof plane must have positive horizontal run")
    return run,rise

def _gable_planes(geometry:BuildingGeometry,volume_id:str)->tuple[RoofPlaneGeometry,RoofPlaneGeometry]:
    planes=[p for p in geometry.roof_planes if p.volume_id==volume_id and p.roof_type is RoofType.GABLE]
    if len(planes)!=2:raise ValueError("BH-025 requires exactly two gable roof planes for the shell volume")
    by={p.side:p for p in planes}
    if set(by)!={"negative","positive"}:raise ValueError("gable roof requires negative and positive planes")
    a,b=by["negative"],by["positive"]
    if a.ridge_direction is None or b.ridge_direction is None or a.ridge_direction is not b.ridge_direction:raise ValueError("gable roof planes must share ridge_direction")
    return a,b

def _footprint(p:GlobalRoofPlacement)->set[tuple[int,int]]:
    part=create_m0_roof_catalog().get(p.part_id); fx,fy=(part.length_studs,part.width_studs) if p.rotation_quarter_turns%2 else (part.width_studs,part.length_studs)
    return {(p.x_studs+dx,p.y_studs+dy) for dx in range(fx) for dy in range(fy)}

def _axis(p:GlobalRoofPlacement,d:RidgeDirection)->int:return p.x_studs if d is RidgeDirection.DEPTH else p.y_studs

def validate_roof_support(roof:SpatialRoof,shell:BuildingBrickShell)->None:
    catalog=create_m0_roof_catalog(); wall_top=shell.walls[0].grid.height_bricks*3
    width=next(r.grid.width_studs for r in shell.walls if r.facade.value=="front"); depth=next(r.grid.width_studs for r in shell.walls if r.facade.value=="right")
    for side in ("negative","positive"):
        ps=[p for p in roof.placements if p.side==side]; axes=sorted({_axis(p,roof.ridge_direction) for p in ps},reverse=side=="positive")
        if not axes:raise ValueError(f"roof side {side!r} has no slope courses")
        courses=[[p for p in ps if _axis(p,roof.ridge_direction)==a] for a in axes]
        if any(p.z_plates!=wall_top for p in courses[0]):raise ValueError(f"roof side {side!r} eave course is not anchored at wall top")
        cells=set().union(*(_footprint(p) for p in courses[0])); edge=(0 if side=="negative" else (width-1 if roof.ridge_direction is RidgeDirection.DEPTH else depth-1))
        touches=any((x==edge if roof.ridge_direction is RidgeDirection.DEPTH else y==edge) for x,y in cells)
        if not touches:raise ValueError(f"roof side {side!r} does not contact its eave wall")
        for prev,current in zip(courses,courses[1:]):
            if not set().union(*(_footprint(p) for p in prev)).intersection(set().union(*(_footprint(p) for p in current))):raise ValueError(f"floating roof course on side {side!r}")
            pz=min(p.z_plates for p in prev); cz=min(p.z_plates for p in current)
            if cz<pz or cz-pz>6:raise ValueError(f"unsupported vertical jump on roof side {side!r}")
            if any(catalog.get(p.part_id).connection_overlap_studs<1 for p in current):raise ValueError("roof part has no connection overlap")
    ridge=[p for p in roof.placements if p.side=="ridge"]
    if not ridge:raise ValueError("roof has no ridge")
    ridge_cells=set().union(*(_footprint(p) for p in ridge))
    for side in ("negative","positive"):
        ps=[p for p in roof.placements if p.side==side]; axes=sorted({_axis(p,roof.ridge_direction) for p in ps},reverse=side=="positive"); inner=axes[-1]
        inner_cells=set().union(*(_footprint(p) for p in ps if _axis(p,roof.ridge_direction)==inner))
        if not ridge_cells.intersection(inner_cells):raise ValueError(f"ridge is not connected to roof side {side!r}")

def generate_spatial_gable_roof(geometry:BuildingGeometry,shell:BuildingBrickShell)->SpatialRoof:
    negative,_=_gable_planes(geometry,shell.volume_id); d=negative.ridge_direction; assert d is not None
    run,rise=_plane_run_and_rise(negative); rise_per_stud=(rise/run)*2.5; wall_top=shell.walls[0].grid.height_bricks*3
    width=next(r.grid.width_studs for r in shell.walls if r.facade.value=="front"); depth=next(r.grid.width_studs for r in shell.walls if r.facade.value=="right")
    span,line=(width,depth) if d is RidgeDirection.DEPTH else (depth,width); half=span//2; placements=[]
    counts={"negative":half,"positive":span-half-1}
    for side in ("negative","positive"):
        for distance in range(counts[side]):
            axis=distance if side=="negative" else span-2-distance; z=wall_top+_round(distance*rise_per_stud)
            for pid,offset,_ in _tile_line(line,"ROOF_SLOPE"):
                placements.append(GlobalRoofPlacement(part_id=pid,side=side,x_studs=axis if d is RidgeDirection.DEPTH else offset,y_studs=offset if d is RidgeDirection.DEPTH else axis,z_plates=z,rotation_quarter_turns=0 if d is RidgeDirection.DEPTH else 1))
    ridge_axis=half; ridge_z=wall_top+_round(max(0,half-1)*rise_per_stud)+1
    for pid,offset,_ in _tile_line(line,"RIDGE_TILE"):
        placements.append(GlobalRoofPlacement(part_id=pid,side="ridge",x_studs=ridge_axis if d is RidgeDirection.DEPTH else offset,y_studs=offset if d is RidgeDirection.DEPTH else ridge_axis,z_plates=ridge_z,rotation_quarter_turns=0 if d is RidgeDirection.DEPTH else 1))
    roof=SpatialRoof(building_id=shell.building_id,roof_id=negative.roof_id,ridge_direction=d,placements=placements);validate_roof_support(roof,shell);return roof
