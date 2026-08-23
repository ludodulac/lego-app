"""Add rich ArchitecturalScene exterior elements to an already-built BrickModel."""
from __future__ import annotations
from math import ceil,floor
import unicodedata
from brickhouse.building.models import Facade
from brickhouse.scene.models import ArchitecturalScene,DeckBoardDirection,EdgeTreatment,ExteriorMaterial,Platform,StairRun
from .brick_model import BrickModel,BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO
EPSILON=1e-6; RAILING_HEIGHT_PLATES=6; RAILING_POST_SPACING_STUDS=3

def _round_half_up(v:float)->int:return int(v+0.5)
def _terrain_extent(profile)->float:return profile.outward_extent if profile.outward_extent is not None else .4
def _scene_bounds(scene):
    xs=[v.position.x for v in scene.volumes];ys=[v.position.y for v in scene.volumes];zs=[v.position.z for v in scene.volumes]
    for p in scene.platforms:xs.append(p.position.x);ys.append(p.position.y);zs.append(0.)
    for s in scene.stairs:xs.extend([s.start.x,s.end.x]);ys.extend([s.start.y,s.end.y]);zs.extend([s.start.z,s.end.z])
    if scene.terrain and scene.terrain.profiles:
        m=scene.volumes[0]
        for profile in scene.terrain.profiles:
            extent=_terrain_extent(profile)
            if profile.facade is Facade.LEFT:xs.append(m.position.x-extent)
            elif profile.facade is Facade.RIGHT:xs.append(m.position.x+m.width.value+extent)
            elif profile.facade is Facade.FRONT:ys.append(m.position.y-extent)
            else:ys.append(m.position.y+m.depth.value+extent)
    return min(xs),min(ys),min(zs)
def _volume_bounds(scene):return min(v.position.x for v in scene.volumes),min(v.position.y for v in scene.volumes),min(v.position.z for v in scene.volumes)
def _nearest_facade(scene,x,y):
    m=scene.volumes[0];l=m.position.x;r=l+m.width.value;f=m.position.y;b=f+m.depth.value
    return min([(abs(x-l),Facade.LEFT),(abs(x-r),Facade.RIGHT),(abs(y-f),Facade.FRONT),(abs(y-b),Facade.REAR)],key=lambda i:i[0])[1]
def _normalized_text(v):return " ".join(unicodedata.normalize("NFKD",v).encode("ascii","ignore").decode("ascii").lower().split())
def _object_text(o,s):return _normalized_text(f"{o.id} {' '.join(e.observation for e in getattr(o,'evidence',[]))} {s.notes or ''}")
def _is_timber(o,s):
    if getattr(o,"material",None) is not None:return o.material is ExteriorMaterial.TIMBER
    return any(t in _object_text(o,s) for t in ("bois","timber","wood","lattes","garde-corps bois"))
def _is_masonry(o,s):
    m=getattr(o,"material",None)
    if m is not None:return m in {ExteriorMaterial.CONCRETE,ExteriorMaterial.MASONRY,ExteriorMaterial.STONE}
    return any(t in _object_text(o,s) for t in ("beton","concrete","maconne","masonry","pierre","muret","enduit"))
def _legacy_platform_treatment(p,s):
    if p.edge_treatment is not None:return p.edge_treatment
    if _is_masonry(p,s) and any(t in _object_text(p,s) for t in ("muret","parapet","garde-corps plein")):return EdgeTreatment.SOLID_PARAPET
    return EdgeTreatment.UNKNOWN
def _stair_edge_treatments(s,scene):
    if s.left_edge is not None or s.right_edge is not None:return s.left_edge or EdgeTreatment.UNKNOWN,s.right_edge or EdgeTreatment.UNKNOWN
    legacy=_is_masonry(s,scene) and any(t in _object_text(s,scene) for t in ("muret","parapet","rampe beton","rampe en beton"))
    return (EdgeTreatment.SOLID_PARAPET,EdgeTreatment.SOLID_PARAPET) if legacy else (EdgeTreatment.UNKNOWN,EdgeTreatment.UNKNOWN)
def _validate_exterior_primitives(scene):
    m=scene.volumes[0];left=m.position.x;right=left+m.width.value;front=m.position.y;rear=front+m.depth.value
    for p in scene.platforms:
        x0=p.position.x;x1=x0+p.width;y0=p.position.y;y1=y0+p.depth;sides=[]
        if x1<=left+EPSILON:sides.append(Facade.LEFT)
        if x0>=right-EPSILON:sides.append(Facade.RIGHT)
        if y1<=front+EPSILON:sides.append(Facade.FRONT)
        if y0>=rear-EPSILON:sides.append(Facade.REAR)
        if not sides:raise ValueError(f"platform {p.id!r} intersects the main building footprint; split attached exterior structures into primitives outside one facade")
        if len(sides)>1:raise ValueError(f"platform {p.id!r} wraps a building corner; split it into one Platform per rectilinear facade segment")
        side=sides[0]
        if side in {Facade.LEFT,Facade.RIGHT} and (y0<front-EPSILON or y1>rear+EPSILON):raise ValueError(f"platform {p.id!r} extends past a side-facade corner; split the geometry")
        if side in {Facade.FRONT,Facade.REAR} and (x0<left-EPSILON or x1>right+EPSILON):raise ValueError(f"platform {p.id!r} extends past a front/rear corner; split the geometry")
    for s in scene.stairs:
        if abs(s.end.x-s.start.x)>EPSILON and abs(s.end.y-s.start.y)>EPSILON:raise ValueError(f"stair {s.id!r} changes two horizontal axes in one run; split turning stairs into axis-aligned StairRun objects joined by a landing")
def _brick(pid,x,y,z,facade,*,part_id="BRICK_1X1",category="brick",rotation=0):return BrickModelPart(placement_id=pid,part_id=part_id,category=category,component="facade_detail",x_studs=max(0,x),y_studs=max(0,y),z_plates=max(0,z),rotation_quarter_turns=rotation,facade=facade)
def _append_unique(parts,seen,part):
    key=(part.x_studs,part.y_studs,part.z_plates)
    if key in seen:return False
    seen.add(key);parts.append(part);return True
def _platform_edge_cells(name,x0,y0,width,depth):
    if name=="x_min":return [(x0,y0+i) for i in range(depth)]
    if name=="x_max":return [(x0+width-1,y0+i) for i in range(depth)]
    if name=="y_min":return [(x0+i,y0) for i in range(width)]
    return [(x0+i,y0+depth-1) for i in range(width)]
def _edge_access_indexes(edge,spm,length):
    blocked=set()
    for span in edge.access_spans:blocked.update(range(max(0,floor(span.from_offset*spm)),min(length,ceil(span.to_offset*spm))))
    return blocked
def _add_platform_edge(parts,seen,*,platform,edge_name,treatment,access_indexes,cells,z0,facade,index):
    if treatment in {EdgeTreatment.NONE,EdgeTreatment.UNKNOWN,EdgeTreatment.WALL_ATTACHED,EdgeTreatment.ACCESS_OPENING}:return index
    guarded=[(i,c) for i,c in enumerate(cells) if i not in access_indexes]
    if treatment is EdgeTreatment.SOLID_PARAPET:
        for _,(x,y) in guarded:
            for z in range(z0+3,z0+RAILING_HEIGHT_PLATES+1,3):
                if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:{edge_name}:parapet:{index:05d}",x,y,z,facade)):index+=1
    elif treatment is EdgeTreatment.OPEN_RAILING:
        gi={i for i,_ in guarded}
        for i,(x,y) in guarded:
            if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:{edge_name}:rail-top:{index:05d}",x,y,z0+RAILING_HEIGHT_PLATES,facade)):index+=1
            if i==0 or i==len(cells)-1 or i-1 not in gi or i+1 not in gi or i%RAILING_POST_SPACING_STUDS==0:
                if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:{edge_name}:rail-post:{index:05d}",x,y,z0+3,facade)):index+=1
    return index
def _deck_direction(platform):
    if platform.deck_board_direction in {DeckBoardDirection.X,DeckBoardDirection.Y}:return platform.deck_board_direction
    return DeckBoardDirection.X if platform.width>=platform.depth else DeckBoardDirection.Y
def _timber_deck(parts,seen,platform,x0,y0,z0,width,depth,facade,index):
    direction=_deck_direction(platform);catalog=((8,"BRICK_1X8"),(6,"BRICK_1X6"),(4,"BRICK_1X4"),(3,"BRICK_1X3"),(2,"BRICK_1X2"),(1,"BRICK_1X1"))
    if direction is DeckBoardDirection.X:
        for dy in range(depth):
            cursor=0
            while cursor<width:
                span,pid=next((n,p) for n,p in catalog if n<=width-cursor);part=_brick(f"scene-platform:{platform.id}:board:{index:05d}",x0+cursor,y0+dy,z0,facade,part_id=pid,rotation=1 if span>1 else 0)
                if _append_unique(parts,seen,part):index+=1
                cursor+=span
    else:
        for dx in range(width):
            cursor=0
            while cursor<depth:
                span,pid=next((n,p) for n,p in catalog if n<=depth-cursor);part=_brick(f"scene-platform:{platform.id}:board:{index:05d}",x0+dx,y0+cursor,z0,facade,part_id=pid,rotation=0)
                if _append_unique(parts,seen,part):index+=1
                cursor+=span
    return index
def _platform_parts(platform,scene,*,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter):
    x0=_round_half_up((platform.position.x-origin_x)*studs_per_meter);y0=_round_half_up((platform.position.y-origin_y)*studs_per_meter);z0=max(0,_round_half_up((platform.position.z-origin_z)*plates_per_meter));width=max(1,_round_half_up(platform.width*studs_per_meter));depth=max(1,_round_half_up(platform.depth*studs_per_meter));facade=_nearest_facade(scene,platform.position.x+platform.width/2,platform.position.y+platform.depth/2);timber=_is_timber(platform,scene);parts=[];index=1;seen=set()
    if timber:index=_timber_deck(parts,seen,platform,x0,y0,z0,width,depth,facade,index)
    else:
        for course in range(max(1,ceil(platform.thickness*plates_per_meter/3.))):
            for dx in range(width):
                for dy in range(depth):
                    if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:deck:{index:05d}",x0+dx,y0+dy,z0+course*3,facade)):index+=1
    for pi,support in enumerate(platform.supports,start=1):
        x=_round_half_up((support.position.x-origin_x)*studs_per_meter);y=_round_half_up((support.position.y-origin_y)*studs_per_meter);z=0
        while z<z0:_append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:support{pi}:{z:04d}",x,y,z,facade));z+=3
    legacy=_legacy_platform_treatment(platform,scene)
    for name in ("x_min","x_max","y_min","y_max"):
        edge=getattr(platform.edges,name) if platform.edges is not None else None;t=edge.treatment if edge is not None else legacy;cells=_platform_edge_cells(name,x0,y0,width,depth);access=_edge_access_indexes(edge,studs_per_meter,len(cells)) if edge is not None else set();index=_add_platform_edge(parts,seen,platform=platform,edge_name=name,treatment=t,access_indexes=access,cells=cells,z0=z0,facade=facade,index=index)
    return parts
def _stair_parts(stair,scene,*,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter):
    sx=_round_half_up((stair.start.x-origin_x)*studs_per_meter);sy=_round_half_up((stair.start.y-origin_y)*studs_per_meter);sz=max(0,_round_half_up((stair.start.z-origin_z)*plates_per_meter));ex=_round_half_up((stair.end.x-origin_x)*studs_per_meter);ey=_round_half_up((stair.end.y-origin_y)*studs_per_meter);ez=max(0,_round_half_up((stair.end.z-origin_z)*plates_per_meter));dx,dy=ex-sx,ey-sy;steps=max(abs(dx),abs(dy),1);width=max(1,_round_half_up(stair.width*studs_per_meter));facade=_nearest_facade(scene,(stair.start.x+stair.end.x)/2,(stair.start.y+stair.end.y)/2);along_x=abs(dx)>=abs(dy);masonry=_is_masonry(stair,scene);left_edge,right_edge=_stair_edge_treatments(stair,scene);parts=[];seen=set();index=1
    for step in range(steps+1):
        t=step/steps;x=_round_half_up(sx+dx*t);y=_round_half_up(sy+dy*t);z=max(0,3*_round_half_up((sz+(ez-sz)*t)/3.));tread=[]
        for offset in range(width):
            px=x if along_x else x+offset;py=y+offset if along_x else y;tread.append((px,py))
            if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:tread:{index:05d}",px,py,z,facade)):index+=1
        if masonry:
            for px,py in tread:
                fill=0
                while fill<z:
                    if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:body:{index:05d}",px,py,fill,facade)):index+=1
                    fill+=3
        for treatment,(px,py),label in ((left_edge,tread[0],"left"),(right_edge,tread[-1],"right")):
            if treatment is EdgeTreatment.SOLID_PARAPET:
                for wz in (z+3,z+6):
                    if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:{label}-parapet:{index:05d}",px,py,wz,facade)):index+=1
            elif treatment is EdgeTreatment.OPEN_RAILING and (step in {0,steps} or step%RAILING_POST_SPACING_STUDS==0):
                for rz in (z+3,z+6):
                    if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:{label}-rail:{index:05d}",px,py,rz,facade)):index+=1
    return parts
def _terrain_parts(scene,*,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter):
    if not scene.terrain or not scene.terrain.profiles:return []
    m=scene.volumes[0];x0=_round_half_up((m.position.x-origin_x)*studs_per_meter);y0=_round_half_up((m.position.y-origin_y)*studs_per_meter);width=max(1,_round_half_up(m.width.value*studs_per_meter));depth=max(1,_round_half_up(m.depth.value*studs_per_meter));parts=[];index=1
    for profile in scene.terrain.profiles:
        band=max(1,_round_half_up(_terrain_extent(profile)*studs_per_meter));length=width if profile.facade in {Facade.FRONT,Facade.REAR} else depth;start=max(0,_round_half_up((profile.start_elevation-origin_z)*plates_per_meter));end=max(0,_round_half_up((profile.end_elevation-origin_z)*plates_per_meter))
        for along in range(length):
            t=along/max(length-1,1);grade=max(0,3*_round_half_up((start+(end-start)*t)/3.))
            for across in range(band):
                if profile.facade is Facade.RIGHT:px,py=x0+width+across,y0+along
                elif profile.facade is Facade.LEFT:px,py=x0-1-across,y0+depth-1-along
                elif profile.facade is Facade.FRONT:px,py=x0+along,y0-1-across
                else:px,py=x0+width-1-along,y0+depth+across
                parts.append(_brick(f"scene-terrain:{profile.facade.value}:{index:06d}",px,py,grade,profile.facade,category="terrain"));index+=1
    return parts
def augment_brick_model_with_scene_architecture(model,scene,*,front_width_studs):
    has_grade=bool(scene.terrain and scene.terrain.profiles)
    if not scene.platforms and not scene.stairs and not has_grade:return model
    if front_width_studs<=0:raise ValueError("front_width_studs must be positive")
    _validate_exterior_primitives(scene);m=scene.volumes[0];spm=front_width_studs/m.width.value;ppm=spm*COURSES_PER_STUD_RATIO*3;ox,oy,oz=_scene_bounds(scene);vx,vy,vz=_volume_bounds(scene);sx=_round_half_up((vx-ox)*spm);sy=_round_half_up((vy-oy)*spm);sz=max(0,_round_half_up((vz-oz)*ppm));shifted=[p.model_copy(update={"x_studs":p.x_studs+sx,"y_studs":p.y_studs+sy,"z_plates":p.z_plates+sz}) for p in model.parts];extra=_terrain_parts(scene,origin_x=ox,origin_y=oy,origin_z=oz,studs_per_meter=spm,plates_per_meter=ppm)
    for p in scene.platforms:extra.extend(_platform_parts(p,scene,origin_x=ox,origin_y=oy,origin_z=oz,studs_per_meter=spm,plates_per_meter=ppm))
    for s in scene.stairs:extra.extend(_stair_parts(s,scene,origin_x=ox,origin_y=oy,origin_z=oz,studs_per_meter=spm,plates_per_meter=ppm))
    allp=shifted+extra;return model.model_copy(update={"width_studs":max(model.width_studs+sx,max(p.x_studs+1 for p in allp)),"depth_studs":max(model.depth_studs+sy,max(p.y_studs+1 for p in allp)),"height_plates":max(model.height_plates+sz,max(p.z_plates+3 for p in allp)),"parts":allp})
