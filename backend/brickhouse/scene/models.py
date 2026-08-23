"""Pydantic contracts for ArchitecturalScene v0.2."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import Appearance, Facade, OpeningType, Position3D, RidgeDirection, RoofType, SourceInfo, WindowStyle

EPSILON = 1e-9
CONNECTIVITY_TOLERANCE_M = 0.12

class Evidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)

class PropertyValue(BaseModel):
    value: float = Field(gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

class SceneVolume(BaseModel):
    id: str
    position: Position3D
    width: PropertyValue
    depth: PropertyValue
    height: PropertyValue
    floors: int = Field(ge=1, le=10)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

class SceneOpening(BaseModel):
    id: str
    type: OpeningType
    volume_id: str
    facade: Facade
    offset_horizontal: float = Field(ge=0)
    offset_vertical: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)
    local_grade_clearance: float | None = None
    window_style: WindowStyle | None = None
    has_sill: bool | None = None
    has_decorative_surround: bool | None = None

    @model_validator(mode="after")
    def validate_window_metadata(self):
        if self.type is not OpeningType.WINDOW and any(v is not None for v in (self.window_style,self.has_sill,self.has_decorative_surround)):
            raise ValueError("window metadata may only be set for window openings")
        return self

class SceneRoof(BaseModel):
    id: str
    volume_id: str
    type: RoofType
    overhang: float = Field(ge=0)
    ridge_direction: RidgeDirection | None = None
    pitch_degrees: float | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)
    @model_validator(mode="after")
    def validate_roof(self):
        if self.type is RoofType.GABLE:
            if self.ridge_direction is None or self.pitch_degrees is None: raise ValueError("gable roof requires ridge_direction and pitch_degrees")
            if not 0 < self.pitch_degrees < 90: raise ValueError("gable roof pitch_degrees must be > 0 and < 90")
        elif self.ridge_direction is not None or self.pitch_degrees is not None: raise ValueError("flat roof must not define gable-only fields")
        return self

class GradeProfile(BaseModel):
    facade: Facade
    start_elevation: float
    end_elevation: float
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

class Terrain(BaseModel):
    kind: Literal["facade_grade_profiles"] = "facade_grade_profiles"
    profiles: list[GradeProfile] = Field(default_factory=list)

class Chimney(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0); depth: float = Field(gt=0); height: float = Field(gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

class ExteriorMaterial(str, Enum):
    TIMBER="timber"; CONCRETE="concrete"; MASONRY="masonry"; STONE="stone"; METAL="metal"; COMPOSITE="composite"; UNKNOWN="unknown"

class DeckBoardDirection(str, Enum):
    X="x"; Y="y"; UNKNOWN="unknown"

class EdgeTreatment(str, Enum):
    NONE="none"; OPEN_RAILING="open_railing"; SOLID_PARAPET="solid_parapet"; WALL_ATTACHED="wall_attached"; ACCESS_OPENING="access_opening"; UNKNOWN="unknown"

class EdgeAccessSpan(BaseModel):
    from_offset: float = Field(ge=0, alias="from")
    to_offset: float = Field(gt=0, alias="to")
    model_config={"populate_by_name":True}
    @model_validator(mode="after")
    def validate_order(self):
        if self.to_offset <= self.from_offset: raise ValueError("edge access span to must be greater than from")
        return self

class PlatformEdge(BaseModel):
    treatment: EdgeTreatment = EdgeTreatment.UNKNOWN
    access_spans: list[EdgeAccessSpan] = Field(default_factory=list)
    @model_validator(mode="after")
    def validate_access(self):
        ordered=sorted(self.access_spans,key=lambda s:s.from_offset)
        for a,b in zip(ordered,ordered[1:]):
            if b.from_offset < a.to_offset-EPSILON: raise ValueError("platform edge access spans must not overlap")
        return self

class PlatformEdges(BaseModel):
    x_min: PlatformEdge = Field(default_factory=PlatformEdge)
    x_max: PlatformEdge = Field(default_factory=PlatformEdge)
    y_min: PlatformEdge = Field(default_factory=PlatformEdge)
    y_max: PlatformEdge = Field(default_factory=PlatformEdge)

class SupportPost(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0); depth: float = Field(gt=0); height: float = Field(gt=0)
    source: SourceInfo

class Platform(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0); depth: float = Field(gt=0); thickness: float = Field(gt=0)
    supports: list[SupportPost] = Field(default_factory=list)
    material: ExteriorMaterial | None = None
    deck_board_direction: DeckBoardDirection | None = None
    edge_treatment: EdgeTreatment | None = None
    edges: PlatformEdges | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)
    @model_validator(mode="after")
    def validate_edge_spans(self):
        if self.edges is None: return self
        for name in ("x_min","x_max"):
            edge=getattr(self.edges,name)
            if any(s.to_offset > self.depth+EPSILON for s in edge.access_spans): raise ValueError(f"platform {self.id!r} access span on {name} exceeds depth")
        for name in ("y_min","y_max"):
            edge=getattr(self.edges,name)
            if any(s.to_offset > self.width+EPSILON for s in edge.access_spans): raise ValueError(f"platform {self.id!r} access span on {name} exceeds width")
        return self

class StairRun(BaseModel):
    id: str
    start: Position3D; end: Position3D
    width: float = Field(gt=0)
    material: ExteriorMaterial | None = None
    left_edge: EdgeTreatment | None = None; right_edge: EdgeTreatment | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

class EquipmentType(str, Enum):
    UTILITY_BOX="utility_box"; PIPE="pipe"; GUTTER="gutter"; DOWNSPOUT="downspout"; VENT="vent"; ANTENNA="antenna"; TEMPORARY_OBJECT="temporary_object"
class FacadeEquipment(BaseModel):
    id:str; type:EquipmentType; facade:Facade|None=None; source:SourceInfo; evidence:list[Evidence]=Field(default_factory=list)
class VisibilityState(str,Enum): VISIBLE="visible"; OCCLUDED="occluded"; UNKNOWN="unknown"
class VisibilitySpan(BaseModel):
    from_offset:float=Field(ge=0,alias="from"); to_offset:float=Field(gt=0,alias="to"); state:VisibilityState; by:str|None=None
    model_config={"populate_by_name":True}
    @model_validator(mode="after")
    def validate_order(self):
        if self.to_offset<=self.from_offset: raise ValueError("visibility span to must be greater than from")
        return self
class FacadeVisibility(BaseModel): facade:Facade; spans:list[VisibilitySpan]=Field(default_factory=list)

class ArchitecturalScene(BaseModel):
    schema_version:Literal["0.2"]; id:str; name:str; units:Literal["m"]="m"
    volumes:list[SceneVolume]=Field(min_length=1); openings:list[SceneOpening]=Field(default_factory=list); roofs:list[SceneRoof]=Field(default_factory=list)
    terrain:Terrain|None=None; chimneys:list[Chimney]=Field(default_factory=list); platforms:list[Platform]=Field(default_factory=list); stairs:list[StairRun]=Field(default_factory=list); equipment:list[FacadeEquipment]=Field(default_factory=list); visibility:list[FacadeVisibility]=Field(default_factory=list); appearance:Appearance; notes:str|None=None
    @model_validator(mode="after")
    def validate_scene(self): self._validate_ids_and_references(); self._validate_opening_geometry(); self._validate_visibility(); self._validate_external_connectivity(); return self
    def _validate_ids_and_references(self):
        ids=[i.id for i in [*self.volumes,*self.openings,*self.roofs,*self.chimneys,*self.platforms,*self.stairs,*self.equipment]]
        for p in self.platforms: ids.extend(s.id for s in p.supports)
        if len(ids)!=len(set(ids)): raise ValueError("scene object IDs must be globally unique")
        volumes={v.id:v for v in self.volumes}; roof_ids=set()
        for o in self.openings:
            if o.volume_id not in volumes: raise ValueError(f"opening {o.id!r} references unknown volume")
        for r in self.roofs:
            if r.volume_id not in volumes: raise ValueError(f"roof {r.id!r} references unknown volume")
            if r.volume_id in roof_ids: raise ValueError("at most one roof may reference a scene volume in v0.2")
            roof_ids.add(r.volume_id)
    def _validate_opening_geometry(self):
        volumes={v.id:v for v in self.volumes}
        for o in self.openings:
            v=volumes[o.volume_id]; span=v.width.value if o.facade in {Facade.FRONT,Facade.REAR} else v.depth.value
            if o.offset_horizontal+o.width>span+EPSILON: raise ValueError(f"opening {o.id!r} extends past facade horizontally")
            if o.offset_vertical+o.height>v.height.value+EPSILON: raise ValueError(f"opening {o.id!r} extends above volume")
        for i,a in enumerate(self.openings):
            for b in self.openings[i+1:]:
                if a.volume_id==b.volume_id and a.facade is b.facade and self._openings_overlap(a,b): raise ValueError(f"openings {a.id!r} and {b.id!r} overlap")
    @staticmethod
    def _openings_overlap(a,b): return a.offset_horizontal<b.offset_horizontal+b.width-EPSILON and b.offset_horizontal<a.offset_horizontal+a.width-EPSILON and a.offset_vertical<b.offset_vertical+b.height-EPSILON and b.offset_vertical<a.offset_vertical+a.height-EPSILON
    def _validate_visibility(self):
        if len({e.facade for e in self.visibility})!=len(self.visibility): raise ValueError("at most one visibility entry may be defined per facade")
        by={e.facade:e for e in self.visibility}
        for e in self.visibility:
            if len(self.volumes)==1:
                v=self.volumes[0]; span=v.width.value if e.facade in {Facade.FRONT,Facade.REAR} else v.depth.value
                if any(s.to_offset>span+EPSILON for s in e.spans): raise ValueError(f"visibility span on {e.facade.value} extends past facade")
            ordered=sorted(e.spans,key=lambda s:s.from_offset)
            for p,c in zip(ordered,ordered[1:]):
                if c.from_offset<p.to_offset-EPSILON: raise ValueError(f"visibility spans overlap on facade {e.facade.value}")
        for o in self.openings:
            e=by.get(o.facade)
            if e:
                for s in e.spans:
                    if o.offset_horizontal<s.to_offset-EPSILON and s.from_offset<o.offset_horizontal+o.width-EPSILON and s.state is not VisibilityState.VISIBLE: raise ValueError(f"opening {o.id!r} intersects non-visible facade span")
    @staticmethod
    def _point_on_platform(pt,p): return p.position.x-CONNECTIVITY_TOLERANCE_M<=pt.x<=p.position.x+p.width+CONNECTIVITY_TOLERANCE_M and p.position.y-CONNECTIVITY_TOLERANCE_M<=pt.y<=p.position.y+p.depth+CONNECTIVITY_TOLERANCE_M and abs(pt.z-p.position.z)<=CONNECTIVITY_TOLERANCE_M
    @staticmethod
    def _point_on_volume_boundary(pt,v):
        x0,x1=v.position.x,v.position.x+v.width.value; y0,y1=v.position.y,v.position.y+v.depth.value; z0,z1=v.position.z,v.position.z+v.height.value
        return x0-CONNECTIVITY_TOLERANCE_M<=pt.x<=x1+CONNECTIVITY_TOLERANCE_M and y0-CONNECTIVITY_TOLERANCE_M<=pt.y<=y1+CONNECTIVITY_TOLERANCE_M and min(abs(pt.x-x0),abs(pt.x-x1),abs(pt.y-y0),abs(pt.y-y1))<=CONNECTIVITY_TOLERANCE_M and z0-CONNECTIVITY_TOLERANCE_M<=pt.z<=z1+CONNECTIVITY_TOLERANCE_M
    @staticmethod
    def _platform_touches_volume(p,v):
        px0,px1=p.position.x,p.position.x+p.width; py0,py1=p.position.y,p.position.y+p.depth; vx0,vx1=v.position.x,v.position.x+v.width.value; vy0,vy1=v.position.y,v.position.y+v.depth.value
        xo=min(px1,vx1)>=max(px0,vx0)-CONNECTIVITY_TOLERANCE_M; yo=min(py1,vy1)>=max(py0,vy0)-CONNECTIVITY_TOLERANCE_M
        return (min(abs(px0-vx1),abs(px1-vx0))<=CONNECTIVITY_TOLERANCE_M and yo) or (min(abs(py0-vy1),abs(py1-vy0))<=CONNECTIVITY_TOLERANCE_M and xo)
    def _validate_external_connectivity(self):
        if not self.platforms and not self.stairs:return
        for p in self.platforms:
            if not any(self._platform_touches_volume(p,v) for v in self.volumes) and not any(self._point_on_platform(s.start,p) or self._point_on_platform(s.end,p) for s in self.stairs): raise ValueError(f"platform {p.id!r} is disconnected from both building and stairs")
        for s in self.stairs:
            for name,pt in (("start",s.start),("end",s.end)):
                if not (any(self._point_on_platform(pt,p) for p in self.platforms) or any(self._point_on_volume_boundary(pt,v) for v in self.volumes) or pt.z<=CONNECTIVITY_TOLERANCE_M): raise ValueError(f"stair {s.id!r} {name} does not connect to ground, a platform, or the building")
