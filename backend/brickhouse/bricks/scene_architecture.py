"""Add rich ArchitecturalScene exterior elements to an already-built BrickModel.

Platforms, stair runs and facade grade profiles are reconstructed from the
validated Scene. New scenes carry structured material and edge metadata; legacy
text hints remain only as a backwards-compatible fallback.
"""
from __future__ import annotations

from math import ceil, floor
import unicodedata

from brickhouse.building.models import Facade
from brickhouse.scene.models import ArchitecturalScene, EdgeTreatment, ExteriorMaterial, Platform, StairRun

from .brick_model import BrickModel, BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO

EPSILON = 1e-6
RAILING_HEIGHT_PLATES = 6
RAILING_POST_SPACING_STUDS = 3


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _scene_bounds(scene: ArchitecturalScene) -> tuple[float, float, float]:
    xs=[v.position.x for v in scene.volumes]; ys=[v.position.y for v in scene.volumes]; zs=[v.position.z for v in scene.volumes]
    for p in scene.platforms: xs.append(p.position.x); ys.append(p.position.y); zs.append(0.0)
    for s in scene.stairs: xs.extend([s.start.x,s.end.x]); ys.extend([s.start.y,s.end.y]); zs.extend([s.start.z,s.end.z])
    if scene.terrain and scene.terrain.profiles:
        main=scene.volumes[0]; facades={p.facade for p in scene.terrain.profiles}
        if Facade.LEFT in facades: xs.append(main.position.x-0.5)
        if Facade.RIGHT in facades: xs.append(main.position.x+main.width.value+0.5)
        if Facade.FRONT in facades: ys.append(main.position.y-0.5)
        if Facade.REAR in facades: ys.append(main.position.y+main.depth.value+0.5)
    return min(xs),min(ys),min(zs)


def _volume_bounds(scene: ArchitecturalScene) -> tuple[float,float,float]:
    return min(v.position.x for v in scene.volumes),min(v.position.y for v in scene.volumes),min(v.position.z for v in scene.volumes)


def _nearest_facade(scene: ArchitecturalScene,x:float,y:float)->Facade:
    main=scene.volumes[0]; left=main.position.x; right=left+main.width.value; front=main.position.y; rear=front+main.depth.value
    return min([(abs(x-left),Facade.LEFT),(abs(x-right),Facade.RIGHT),(abs(y-front),Facade.FRONT),(abs(y-rear),Facade.REAR)],key=lambda i:i[0])[1]


def _normalized_text(value:str)->str:
    return " ".join(unicodedata.normalize("NFKD",value).encode("ascii","ignore").decode("ascii").lower().split())


def _object_text(obj,scene:ArchitecturalScene)->str:
    evidence=" ".join(item.observation for item in getattr(obj,"evidence",[]))
    return _normalized_text(f"{obj.id} {evidence} {scene.notes or ''}")


def _is_timber(obj,scene:ArchitecturalScene)->bool:
    if getattr(obj,"material",None) is not None: return obj.material is ExteriorMaterial.TIMBER
    return any(t in _object_text(obj,scene) for t in ("bois","timber","wood","lattes","garde-corps bois"))


def _is_masonry(obj,scene:ArchitecturalScene)->bool:
    material=getattr(obj,"material",None)
    if material is not None: return material in {ExteriorMaterial.CONCRETE,ExteriorMaterial.MASONRY,ExteriorMaterial.STONE}
    return any(t in _object_text(obj,scene) for t in ("beton","concrete","maconne","masonry","pierre","muret","enduit"))


def _legacy_platform_treatment(platform:Platform,scene:ArchitecturalScene)->EdgeTreatment:
    if platform.edge_treatment is not None: return platform.edge_treatment
    if _is_masonry(platform,scene) and any(t in _object_text(platform,scene) for t in ("muret","parapet","garde-corps plein")):
        return EdgeTreatment.SOLID_PARAPET
    return EdgeTreatment.UNKNOWN


def _stair_edge_treatments(stair:StairRun,scene:ArchitecturalScene)->tuple[EdgeTreatment,EdgeTreatment]:
    if stair.left_edge is not None or stair.right_edge is not None:
        return stair.left_edge or EdgeTreatment.UNKNOWN,stair.right_edge or EdgeTreatment.UNKNOWN
    legacy=_is_masonry(stair,scene) and any(t in _object_text(stair,scene) for t in ("muret","parapet","rampe beton","rampe en beton"))
    return (EdgeTreatment.SOLID_PARAPET,EdgeTreatment.SOLID_PARAPET) if legacy else (EdgeTreatment.UNKNOWN,EdgeTreatment.UNKNOWN)


def _validate_exterior_primitives(scene:ArchitecturalScene)->None:
    main=scene.volumes[0]; left=main.position.x; right=left+main.width.value; front=main.position.y; rear=front+main.depth.value
    for p in scene.platforms:
        x0=p.position.x; x1=x0+p.width; y0=p.position.y; y1=y0+p.depth; sides=[]
        if x1<=left+EPSILON:sides.append(Facade.LEFT)
        if x0>=right-EPSILON:sides.append(Facade.RIGHT)
        if y1<=front+EPSILON:sides.append(Facade.FRONT)
        if y0>=rear-EPSILON:sides.append(Facade.REAR)
        if not sides: raise ValueError(f"platform {p.id!r} intersects the main building footprint; split attached exterior structures into primitives outside one facade")
        if len(sides)>1: raise ValueError(f"platform {p.id!r} wraps a building corner; split it into one Platform per rectilinear facade segment")
        side=sides[0]
        if side in {Facade.LEFT,Facade.RIGHT} and (y0<front-EPSILON or y1>rear+EPSILON): raise ValueError(f"platform {p.id!r} extends past a side-facade corner; split the geometry")
        if side in {Facade.FRONT,Facade.REAR} and (x0<left-EPSILON or x1>right+EPSILON): raise ValueError(f"platform {p.id!r} extends past a front/rear corner; split the geometry")
    for s in scene.stairs:
        if abs(s.end.x-s.start.x)>EPSILON and abs(s.end.y-s.start.y)>EPSILON:
            raise ValueError(f"stair {s.id!r} changes two horizontal axes in one run; split turning stairs into axis-aligned StairRun objects joined by a landing")


def _brick(placement_id:str,x:int,y:int,z:int,facade:Facade,*,part_id:str="BRICK_1X1",category:str="brick")->BrickModelPart:
    return BrickModelPart(placement_id=placement_id,part_id=part_id,category=category,component="facade_detail",x_studs=max(0,x),y_studs=max(0,y),z_plates=max(0,z),rotation_quarter_turns=0,facade=facade)


def _append_unique(parts:list[BrickModelPart],seen:set[tuple[int,int,int]],part:BrickModelPart)->bool:
    key=(part.x_studs,part.y_studs,part.z_plates)
    if key in seen:return False
    seen.add(key);parts.append(part);return True


def _platform_edge_cells(name:str,x0:int,y0:int,width:int,depth:int)->list[tuple[int,int]]:
    if name=="x_min": return [(x0,y0+i) for i in range(depth)]
    if name=="x_max": return [(x0+width-1,y0+i) for i in range(depth)]
    if name=="y_min": return [(x0+i,y0) for i in range(width)]
    return [(x0+i,y0+depth-1) for i in range(width)]


def _edge_access_indexes(edge,studs_per_meter:float,length:int)->set[int]:
    blocked:set[int]=set()
    for span in edge.access_spans:
        start=max(0,floor(span.from_offset*studs_per_meter))
        end=min(length,ceil(span.to_offset*studs_per_meter))
        blocked.update(range(start,end))
    return blocked


def _add_platform_edge(parts:list[BrickModelPart],seen:set[tuple[int,int,int]],*,platform:Platform,edge_name:str,treatment:EdgeTreatment,access_indexes:set[int],cells:list[tuple[int,int]],z0:int,facade:Facade,index:int)->int:
    if treatment in {EdgeTreatment.NONE,EdgeTreatment.UNKNOWN,EdgeTreatment.WALL_ATTACHED,EdgeTreatment.ACCESS_OPENING}:
        return index
    guarded=[(i,cell) for i,cell in enumerate(cells) if i not in access_indexes]
    if treatment is EdgeTreatment.SOLID_PARAPET:
        for _,(x,y) in guarded:
            for z in range(z0+3,z0+RAILING_HEIGHT_PLATES+1,3):
                part=_brick(f"scene-platform:{platform.id}:{edge_name}:parapet:{index:05d}",x,y,z,facade)
                if _append_unique(parts,seen,part):index+=1
        return index
    if treatment is EdgeTreatment.OPEN_RAILING:
        guarded_indexes={i for i,_ in guarded}
        for i,(x,y) in guarded:
            # Continuous top rail, but only sparse vertical posts below it.
            top=_brick(f"scene-platform:{platform.id}:{edge_name}:rail-top:{index:05d}",x,y,z0+RAILING_HEIGHT_PLATES,facade)
            if _append_unique(parts,seen,top):index+=1
            boundary=i==0 or i==len(cells)-1 or i-1 not in guarded_indexes or i+1 not in guarded_indexes
            if boundary or i%RAILING_POST_SPACING_STUDS==0:
                post=_brick(f"scene-platform:{platform.id}:{edge_name}:rail-post:{index:05d}",x,y,z0+3,facade)
                if _append_unique(parts,seen,post):index+=1
    return index


def _platform_parts(platform:Platform,scene:ArchitecturalScene,*,origin_x:float,origin_y:float,origin_z:float,studs_per_meter:float,plates_per_meter:float)->list[BrickModelPart]:
    x0=_round_half_up((platform.position.x-origin_x)*studs_per_meter); y0=_round_half_up((platform.position.y-origin_y)*studs_per_meter); z0=max(0,_round_half_up((platform.position.z-origin_z)*plates_per_meter))
    width=max(1,_round_half_up(platform.width*studs_per_meter)); depth=max(1,_round_half_up(platform.depth*studs_per_meter)); facade=_nearest_facade(scene,platform.position.x+platform.width/2,platform.position.y+platform.depth/2)
    timber=_is_timber(platform,scene); parts=[]; index=1; seen:set[tuple[int,int,int]]=set()
    courses=1 if timber else max(1,ceil(platform.thickness*plates_per_meter/3.0))
    for course in range(courses):
        z=z0+course*3
        for dx in range(width):
            for dy in range(depth):
                part=_brick(f"scene-platform:{platform.id}:deck:{index:05d}",x0+dx,y0+dy,z,facade)
                if _append_unique(parts,seen,part):index+=1
    for post_index,support in enumerate(platform.supports,start=1):
        x=_round_half_up((support.position.x-origin_x)*studs_per_meter); y=_round_half_up((support.position.y-origin_y)*studs_per_meter); z=0
        while z<z0:
            part=_brick(f"scene-platform:{platform.id}:support{post_index}:{z:04d}",x,y,z,facade)
            _append_unique(parts,seen,part); z+=3
    legacy=_legacy_platform_treatment(platform,scene)
    for name in ("x_min","x_max","y_min","y_max"):
        edge=getattr(platform.edges,name) if platform.edges is not None else None
        treatment=edge.treatment if edge is not None else legacy
        cells=_platform_edge_cells(name,x0,y0,width,depth)
        access=_edge_access_indexes(edge,studs_per_meter,len(cells)) if edge is not None else set()
        index=_add_platform_edge(parts,seen,platform=platform,edge_name=name,treatment=treatment,access_indexes=access,cells=cells,z0=z0,facade=facade,index=index)
    return parts


def _stair_parts(stair:StairRun,scene:ArchitecturalScene,*,origin_x:float,origin_y:float,origin_z:float,studs_per_meter:float,plates_per_meter:float)->list[BrickModelPart]:
    sx=_round_half_up((stair.start.x-origin_x)*studs_per_meter); sy=_round_half_up((stair.start.y-origin_y)*studs_per_meter); sz=max(0,_round_half_up((stair.start.z-origin_z)*plates_per_meter))
    ex=_round_half_up((stair.end.x-origin_x)*studs_per_meter); ey=_round_half_up((stair.end.y-origin_y)*studs_per_meter); ez=max(0,_round_half_up((stair.end.z-origin_z)*plates_per_meter))
    dx,dy=ex-sx,ey-sy; steps=max(abs(dx),abs(dy),1); width=max(1,_round_half_up(stair.width*studs_per_meter)); facade=_nearest_facade(scene,(stair.start.x+stair.end.x)/2,(stair.start.y+stair.end.y)/2); along_x=abs(dx)>=abs(dy); masonry=_is_masonry(stair,scene)
    left_edge,right_edge=_stair_edge_treatments(stair,scene); parts=[]; seen:set[tuple[int,int,int]]=set(); index=1
    for step in range(steps+1):
        t=step/steps; x=_round_half_up(sx+dx*t); y=_round_half_up(sy+dy*t); z=max(0,3*_round_half_up((sz+(ez-sz)*t)/3.0)); tread=[]
        for offset in range(width):
            px=x if along_x else x+offset; py=y+offset if along_x else y; tread.append((px,py)); part=_brick(f"scene-stair:{stair.id}:tread:{index:05d}",px,py,z,facade)
            if _append_unique(parts,seen,part):index+=1
        if masonry:
            for px,py in tread:
                fill=0
                while fill<z:
                    part=_brick(f"scene-stair:{stair.id}:body:{index:05d}",px,py,fill,facade)
                    if _append_unique(parts,seen,part):index+=1
                    fill+=3
        if tread:
            for treatment,(px,py),label in ((left_edge,tread[0],"left"),(right_edge,tread[-1],"right")):
                if treatment is EdgeTreatment.SOLID_PARAPET:
                    for wall_z in (z+3,z+6):
                        part=_brick(f"scene-stair:{stair.id}:{label}-parapet:{index:05d}",px,py,wall_z,facade)
                        if _append_unique(parts,seen,part):index+=1
                elif treatment is EdgeTreatment.OPEN_RAILING and (step in {0,steps} or step%RAILING_POST_SPACING_STUDS==0):
                    for rail_z in (z+3,z+6):
                        part=_brick(f"scene-stair:{stair.id}:{label}-rail:{index:05d}",px,py,rail_z,facade)
                        if _append_unique(parts,seen,part):index+=1
    return parts


def _terrain_parts(scene:ArchitecturalScene,*,origin_x:float,origin_y:float,origin_z:float,studs_per_meter:float,plates_per_meter:float)->list[BrickModelPart]:
    if not scene.terrain or not scene.terrain.profiles:return []
    main=scene.volumes[0]; x0=_round_half_up((main.position.x-origin_x)*studs_per_meter); y0=_round_half_up((main.position.y-origin_y)*studs_per_meter); width=max(1,_round_half_up(main.width.value*studs_per_meter)); depth=max(1,_round_half_up(main.depth.value*studs_per_meter)); band=max(1,_round_half_up(0.4*studs_per_meter)); parts=[]; index=1
    for profile in scene.terrain.profiles:
        length=width if profile.facade in {Facade.FRONT,Facade.REAR} else depth
        start_z=max(0,_round_half_up((profile.start_elevation-origin_z)*plates_per_meter)); end_z=max(0,_round_half_up((profile.end_elevation-origin_z)*plates_per_meter))
        for along in range(length):
            t=along/max(length-1,1); grade=max(0,3*_round_half_up((start_z+(end_z-start_z)*t)/3.0))
            for across in range(band):
                if profile.facade is Facade.RIGHT:px,py=x0+width+across,y0+along
                elif profile.facade is Facade.LEFT:px,py=x0-1-across,y0+depth-1-along
                elif profile.facade is Facade.FRONT:px,py=x0+along,y0-1-across
                else:px,py=x0+width-1-along,y0+depth+across
                parts.append(_brick(f"scene-terrain:{profile.facade.value}:{index:06d}",px,py,grade,profile.facade,category="facade_detail")); index+=1
    return parts


def augment_brick_model_with_scene_architecture(model:BrickModel,scene:ArchitecturalScene,*,front_width_studs:int)->BrickModel:
    has_grade=bool(scene.terrain and scene.terrain.profiles)
    if not scene.platforms and not scene.stairs and not has_grade:return model
    if front_width_studs<=0:raise ValueError("front_width_studs must be positive")
    _validate_exterior_primitives(scene)
    main=scene.volumes[0]; studs_per_meter=front_width_studs/main.width.value; plates_per_meter=studs_per_meter*COURSES_PER_STUD_RATIO*3
    origin_x,origin_y,origin_z=_scene_bounds(scene); volume_x,volume_y,volume_z=_volume_bounds(scene); shift_x=_round_half_up((volume_x-origin_x)*studs_per_meter); shift_y=_round_half_up((volume_y-origin_y)*studs_per_meter); shift_z=max(0,_round_half_up((volume_z-origin_z)*plates_per_meter))
    shifted=[p.model_copy(update={"x_studs":p.x_studs+shift_x,"y_studs":p.y_studs+shift_y,"z_plates":p.z_plates+shift_z}) for p in model.parts]
    extra=[]; extra.extend(_terrain_parts(scene,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter))
    for p in scene.platforms:extra.extend(_platform_parts(p,scene,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter))
    for s in scene.stairs:extra.extend(_stair_parts(s,scene,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter))
    all_parts=shifted+extra; width_out=max(model.width_studs+shift_x,max(p.x_studs+1 for p in all_parts)); depth_out=max(model.depth_studs+shift_y,max(p.y_studs+1 for p in all_parts)); height_out=max(model.height_plates+shift_z,max(p.z_plates+3 for p in all_parts))
    return model.model_copy(update={"width_studs":width_out,"depth_studs":depth_out,"height_plates":height_out,"parts":all_parts})
