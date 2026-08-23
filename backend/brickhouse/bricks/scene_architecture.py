"""Add rich ArchitecturalScene exterior elements to an already-built BrickModel.

The Scene remains the geometric source of truth. Exterior primitives are
quantized onto the LEGO grid without inventing missing supports, railings or
connections.
"""
from __future__ import annotations

from math import ceil, floor
import unicodedata

from brickhouse.building.models import Facade
from brickhouse.scene.models import ArchitecturalScene, DeckBoardDirection, EdgeTreatment, ExteriorMaterial, Platform, StairRun
from .brick_model import BrickModel, BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO

EPSILON = 1e-6
RAILING_HEIGHT_PLATES = 6
RAILING_POST_SPACING_STUDS = 3


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _course_z(metric_z: float, origin_z: float, plates_per_meter: float) -> int:
    """Quantize a walkable architectural level to the shared 3-plate brick course."""
    raw = (metric_z - origin_z) * plates_per_meter
    return max(0, 3 * _round_half_up(raw / 3.0))


def _terrain_extent(profile) -> float:
    return profile.outward_extent if profile.outward_extent is not None else 0.4


def _scene_bounds(scene: ArchitecturalScene) -> tuple[float, float, float]:
    xs = [v.position.x for v in scene.volumes]
    ys = [v.position.y for v in scene.volumes]
    zs = [v.position.z for v in scene.volumes]
    for platform in scene.platforms:
        xs.append(platform.position.x)
        ys.append(platform.position.y)
        zs.append(platform.position.z)
    for stair in scene.stairs:
        dx = abs(stair.end.x - stair.start.x)
        dy = abs(stair.end.y - stair.start.y)
        half = stair.width / 2
        if dx >= dy:
            xs.extend([stair.start.x, stair.end.x])
            ys.extend([stair.start.y-half, stair.start.y+half, stair.end.y-half, stair.end.y+half])
        else:
            ys.extend([stair.start.y, stair.end.y])
            xs.extend([stair.start.x-half, stair.start.x+half, stair.end.x-half, stair.end.x+half])
        zs.extend([stair.start.z, stair.end.z])
    if scene.terrain and scene.terrain.profiles:
        main = scene.volumes[0]
        for profile in scene.terrain.profiles:
            zs.extend([profile.start_elevation, profile.end_elevation])
            extent = _terrain_extent(profile)
            if profile.facade is Facade.LEFT:
                xs.append(main.position.x - extent)
            elif profile.facade is Facade.RIGHT:
                xs.append(main.position.x + main.width.value + extent)
            elif profile.facade is Facade.FRONT:
                ys.append(main.position.y - extent)
            else:
                ys.append(main.position.y + main.depth.value + extent)
    return min(xs), min(ys), min(zs)


def _volume_bounds(scene: ArchitecturalScene) -> tuple[float, float, float]:
    return min(v.position.x for v in scene.volumes), min(v.position.y for v in scene.volumes), min(v.position.z for v in scene.volumes)


def _nearest_facade(scene: ArchitecturalScene, x: float, y: float) -> Facade:
    main = scene.volumes[0]
    left, right = main.position.x, main.position.x + main.width.value
    front, rear = main.position.y, main.position.y + main.depth.value
    return min([(abs(x-left),Facade.LEFT),(abs(x-right),Facade.RIGHT),(abs(y-front),Facade.FRONT),(abs(y-rear),Facade.REAR)],key=lambda item:item[0])[1]


def _normalized_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower().split())


def _object_text(obj, scene: ArchitecturalScene) -> str:
    evidence = " ".join(item.observation for item in getattr(obj, "evidence", []))
    return _normalized_text(f"{obj.id} {evidence} {scene.notes or ''}")


def _is_timber(obj, scene: ArchitecturalScene) -> bool:
    if getattr(obj, "material", None) is not None:
        return obj.material is ExteriorMaterial.TIMBER
    return any(token in _object_text(obj, scene) for token in ("bois","timber","wood","lattes","garde-corps bois"))


def _is_masonry(obj, scene: ArchitecturalScene) -> bool:
    material = getattr(obj, "material", None)
    if material is not None:
        return material in {ExteriorMaterial.CONCRETE, ExteriorMaterial.MASONRY, ExteriorMaterial.STONE}
    return any(token in _object_text(obj, scene) for token in ("beton","concrete","maconne","masonry","pierre","muret","enduit"))


def _legacy_platform_treatment(platform: Platform, scene: ArchitecturalScene) -> EdgeTreatment:
    if platform.edge_treatment is not None:
        return platform.edge_treatment
    if _is_masonry(platform, scene) and any(token in _object_text(platform, scene) for token in ("muret","parapet","garde-corps plein")):
        return EdgeTreatment.SOLID_PARAPET
    return EdgeTreatment.UNKNOWN


def _stair_edge_treatments(stair: StairRun, scene: ArchitecturalScene) -> tuple[EdgeTreatment, EdgeTreatment]:
    if stair.left_edge is not None or stair.right_edge is not None:
        return stair.left_edge or EdgeTreatment.UNKNOWN, stair.right_edge or EdgeTreatment.UNKNOWN
    legacy = _is_masonry(stair, scene) and any(token in _object_text(stair, scene) for token in ("muret","parapet","rampe beton","rampe en beton"))
    return (EdgeTreatment.SOLID_PARAPET, EdgeTreatment.SOLID_PARAPET) if legacy else (EdgeTreatment.UNKNOWN, EdgeTreatment.UNKNOWN)


def _validate_exterior_primitives(scene: ArchitecturalScene) -> None:
    main=scene.volumes[0]; left=main.position.x; right=left+main.width.value; front=main.position.y; rear=front+main.depth.value
    for platform in scene.platforms:
        x0=platform.position.x; x1=x0+platform.width; y0=platform.position.y; y1=y0+platform.depth; sides=[]
        if x1<=left+EPSILON:sides.append(Facade.LEFT)
        if x0>=right-EPSILON:sides.append(Facade.RIGHT)
        if y1<=front+EPSILON:sides.append(Facade.FRONT)
        if y0>=rear-EPSILON:sides.append(Facade.REAR)
        if not sides: raise ValueError(f"platform {platform.id!r} intersects the main building footprint; split attached exterior structures into primitives outside one facade")
        if len(sides)>1: raise ValueError(f"platform {platform.id!r} wraps a building corner; split it into one Platform per rectilinear facade segment")
        side=sides[0]
        if side in {Facade.LEFT,Facade.RIGHT} and (y0<front-EPSILON or y1>rear+EPSILON): raise ValueError(f"platform {platform.id!r} extends past a side-facade corner; split the geometry")
        if side in {Facade.FRONT,Facade.REAR} and (x0<left-EPSILON or x1>right+EPSILON): raise ValueError(f"platform {platform.id!r} extends past a front/rear corner; split the geometry")
    for stair in scene.stairs:
        if abs(stair.end.x-stair.start.x)>EPSILON and abs(stair.end.y-stair.start.y)>EPSILON:
            raise ValueError(f"stair {stair.id!r} changes two horizontal axes in one run; split turning stairs into axis-aligned StairRun objects joined by a landing")


def _brick(placement_id:str,x:int,y:int,z:int,facade:Facade,*,part_id:str="BRICK_1X1",category:str="brick",rotation:int=0)->BrickModelPart:
    return BrickModelPart(placement_id=placement_id,part_id=part_id,category=category,component="facade_detail",x_studs=max(0,x),y_studs=max(0,y),z_plates=max(0,z),rotation_quarter_turns=rotation,facade=facade)


def _append_unique(parts:list[BrickModelPart],seen:set[tuple[int,int,int]],part:BrickModelPart)->bool:
    key=(part.x_studs,part.y_studs,part.z_plates)
    if key in seen:return False
    seen.add(key);parts.append(part);return True


def _platform_edge_cells(name:str,x0:int,y0:int,width:int,depth:int)->list[tuple[int,int]]:
    if name=="x_min":return [(x0,y0+i) for i in range(depth)]
    if name=="x_max":return [(x0+width-1,y0+i) for i in range(depth)]
    if name=="y_min":return [(x0+i,y0) for i in range(width)]
    return [(x0+i,y0+depth-1) for i in range(width)]


def _edge_access_indexes(edge,studs_per_meter:float,length:int)->set[int]:
    access=set()
    for span in edge.access_spans:
        access.update(range(max(0,floor(span.from_offset*studs_per_meter)),min(length,ceil(span.to_offset*studs_per_meter))))
    return access


def _add_platform_edge(parts,seen,*,platform,edge_name,treatment,access_indexes,cells,z0,facade,index):
    if treatment in {EdgeTreatment.NONE,EdgeTreatment.UNKNOWN,EdgeTreatment.WALL_ATTACHED,EdgeTreatment.ACCESS_OPENING}:return index
    guarded=[(i,cell) for i,cell in enumerate(cells) if i not in access_indexes]
    if treatment is EdgeTreatment.SOLID_PARAPET:
        for _,(x,y) in guarded:
            for z in range(z0+3,z0+RAILING_HEIGHT_PLATES+1,3):
                if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:{edge_name}:parapet:{index:05d}",x,y,z,facade)):index+=1
    elif treatment is EdgeTreatment.OPEN_RAILING:
        guarded_indexes={i for i,_ in guarded}
        for i,(x,y) in guarded:
            if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:{edge_name}:rail-top:{index:05d}",x,y,z0+RAILING_HEIGHT_PLATES,facade)):index+=1
            if i==0 or i==len(cells)-1 or i-1 not in guarded_indexes or i+1 not in guarded_indexes or i%RAILING_POST_SPACING_STUDS==0:
                if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:{edge_name}:rail-post:{index:05d}",x,y,z0+3,facade)):index+=1
    return index


def _deck_direction(platform:Platform)->DeckBoardDirection:
    if platform.deck_board_direction in {DeckBoardDirection.X,DeckBoardDirection.Y}:return platform.deck_board_direction
    return DeckBoardDirection.X if platform.width>=platform.depth else DeckBoardDirection.Y


def _timber_deck(parts,seen,platform,x0,y0,z0,width,depth,facade,index):
    direction=_deck_direction(platform);catalog=((8,"BRICK_1X8"),(6,"BRICK_1X6"),(4,"BRICK_1X4"),(3,"BRICK_1X3"),(2,"BRICK_1X2"),(1,"BRICK_1X1"))
    if direction is DeckBoardDirection.X:
        for dy in range(depth):
            cursor=0
            while cursor<width:
                span,part_id=next((n,pid) for n,pid in catalog if n<=width-cursor)
                if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:board:{index:05d}",x0+cursor,y0+dy,z0,facade,part_id=part_id,rotation=1 if span>1 else 0)):index+=1
                cursor+=span
    else:
        for dx in range(width):
            cursor=0
            while cursor<depth:
                span,part_id=next((n,pid) for n,pid in catalog if n<=depth-cursor)
                if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:board:{index:05d}",x0+dx,y0+cursor,z0,facade,part_id=part_id)):index+=1
                cursor+=span
    return index


def _masonry_platform_course_bases(platform:Platform,z0:int,plates_per_meter:float)->list[int]:
    courses=max(1,ceil(platform.thickness*plates_per_meter/3.0))
    return [z for z in range(z0-3*(courses-1),z0+1,3) if z>=0]


def _add_supports(parts,seen,*,platform,facade,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter,platform_z):
    for support_index,support in enumerate(platform.supports,start=1):
        x0=_round_half_up((support.position.x-origin_x)*studs_per_meter); y0=_round_half_up((support.position.y-origin_y)*studs_per_meter)
        width=max(1,_round_half_up(support.width*studs_per_meter)); depth=max(1,_round_half_up(support.depth*studs_per_meter))
        base_z=max(0,_round_half_up((support.position.z-origin_z)*plates_per_meter)); declared_top=max(base_z,_round_half_up((support.position.z+support.height-origin_z)*plates_per_meter)); top_z=min(platform_z,declared_top)
        for dx in range(width):
            for dy in range(depth):
                z=base_z
                while z<top_z:
                    _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:support{support_index}:{dx}:{dy}:{z:04d}",x0+dx,y0+dy,z,facade));z+=3


def _platform_parts(platform:Platform,scene:ArchitecturalScene,*,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter)->list[BrickModelPart]:
    x0=_round_half_up((platform.position.x-origin_x)*studs_per_meter); y0=_round_half_up((platform.position.y-origin_y)*studs_per_meter)
    # Platforms and StairRun endpoints share one course quantizer. This prevents a
    # metrically connected landing at e.g. 13.8 raw plates from becoming z=14
    # while the stair endpoint becomes z=15.
    z0=_course_z(platform.position.z,origin_z,plates_per_meter)
    width=max(1,_round_half_up(platform.width*studs_per_meter)); depth=max(1,_round_half_up(platform.depth*studs_per_meter)); facade=_nearest_facade(scene,platform.position.x+platform.width/2,platform.position.y+platform.depth/2)
    parts=[];index=1;seen=set()
    if _is_timber(platform,scene):index=_timber_deck(parts,seen,platform,x0,y0,z0,width,depth,facade,index)
    else:
        for course_z in _masonry_platform_course_bases(platform,z0,plates_per_meter):
            for dx in range(width):
                for dy in range(depth):
                    if _append_unique(parts,seen,_brick(f"scene-platform:{platform.id}:deck:{index:05d}",x0+dx,y0+dy,course_z,facade)):index+=1
    _add_supports(parts,seen,platform=platform,facade=facade,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter,platform_z=z0)
    legacy=_legacy_platform_treatment(platform,scene)
    for name in ("x_min","x_max","y_min","y_max"):
        edge=getattr(platform.edges,name) if platform.edges is not None else None;treatment=edge.treatment if edge is not None else legacy;cells=_platform_edge_cells(name,x0,y0,width,depth);access=_edge_access_indexes(edge,studs_per_meter,len(cells)) if edge is not None else set()
        index=_add_platform_edge(parts,seen,platform=platform,edge_name=name,treatment=treatment,access_indexes=access,cells=cells,z0=z0,facade=facade,index=index)
    return parts


def _stair_tread_geometry(x:int,y:int,width:int,dx:int,dy:int)->tuple[list[tuple[int,int]],tuple[int,int],tuple[int,int]]:
    start_offset=-(width//2)
    if abs(dx)>=abs(dy):
        cells=[(x,y+start_offset+offset) for offset in range(width)];low,high=cells[0],cells[-1]
        return (cells,high,low) if dx>=0 else (cells,low,high)
    cells=[(x+start_offset+offset,y) for offset in range(width)];low,high=cells[0],cells[-1]
    return (cells,low,high) if dy>=0 else (cells,high,low)


def _stair_parts(stair:StairRun,scene:ArchitecturalScene,*,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter)->list[BrickModelPart]:
    sx=_round_half_up((stair.start.x-origin_x)*studs_per_meter);sy=_round_half_up((stair.start.y-origin_y)*studs_per_meter);sz=_course_z(stair.start.z,origin_z,plates_per_meter)
    ex=_round_half_up((stair.end.x-origin_x)*studs_per_meter);ey=_round_half_up((stair.end.y-origin_y)*studs_per_meter);ez=_course_z(stair.end.z,origin_z,plates_per_meter)
    dx,dy=ex-sx,ey-sy;steps=max(abs(dx),abs(dy),1);width=max(1,_round_half_up(stair.width*studs_per_meter));facade=_nearest_facade(scene,(stair.start.x+stair.end.x)/2,(stair.start.y+stair.end.y)/2);masonry=_is_masonry(stair,scene);left_edge,right_edge=_stair_edge_treatments(stair,scene);parts=[];seen=set();index=1
    for step in range(steps+1):
        t=step/steps;x=_round_half_up(sx+dx*t);y=_round_half_up(sy+dy*t);z=3*_round_half_up((sz+(ez-sz)*t)/3.0);tread,left_cell,right_cell=_stair_tread_geometry(x,y,width,dx,dy)
        for px,py in tread:
            if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:tread:{index:05d}",px,py,z,facade)):index+=1
        if masonry:
            for px,py in tread:
                fill=0
                while fill<z:
                    if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:body:{index:05d}",px,py,fill,facade)):index+=1
                    fill+=3
        for treatment,(px,py),label in ((left_edge,left_cell,"left"),(right_edge,right_cell,"right")):
            if treatment is EdgeTreatment.SOLID_PARAPET:
                for wall_z in (z+3,z+6):
                    if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:{label}-parapet:{index:05d}",px,py,wall_z,facade)):index+=1
            elif treatment is EdgeTreatment.OPEN_RAILING and (step in {0,steps} or step%RAILING_POST_SPACING_STUDS==0):
                for rail_z in (z+3,z+6):
                    if _append_unique(parts,seen,_brick(f"scene-stair:{stair.id}:{label}-rail:{index:05d}",px,py,rail_z,facade)):index+=1
    return parts


def _terrain_parts(scene:ArchitecturalScene,*,origin_x,origin_y,origin_z,studs_per_meter,plates_per_meter)->list[BrickModelPart]:
    if not scene.terrain or not scene.terrain.profiles:return []
    main=scene.volumes[0];x0=_round_half_up((main.position.x-origin_x)*studs_per_meter);y0=_round_half_up((main.position.y-origin_y)*studs_per_meter);width=max(1,_round_half_up(main.width.value*studs_per_meter));depth=max(1,_round_half_up(main.depth.value*studs_per_meter));parts=[];index=1
    for profile in scene.terrain.profiles:
        band=max(1,_round_half_up(_terrain_extent(profile)*studs_per_meter));length=width if profile.facade in {Facade.FRONT,Facade.REAR} else depth;start=_course_z(profile.start_elevation,origin_z,plates_per_meter);end=_course_z(profile.end_elevation,origin_z,plates_per_meter)
        for along in range(length):
            t=along/max(length-1,1);grade=3*_round_half_up((start+(end-start)*t)/3.0)
            for across in range(band):
                if profile.facade is Facade.RIGHT:px,py=x0+width+across,y0+along
                elif profile.facade is Facade.LEFT:px,py=x0-1-across,y0+depth-1-along
                elif profile.facade is Facade.FRONT:px,py=x0+along,y0-1-across
                else:px,py=x0+width-1-along,y0+depth+across
                parts.append(_brick(f"scene-terrain:{profile.facade.value}:{index:06d}",px,py,grade,profile.facade,category="terrain"));index+=1
    return parts


def augment_brick_model_with_scene_architecture(model:BrickModel,scene:ArchitecturalScene,*,front_width_studs:int)->BrickModel:
    has_grade=bool(scene.terrain and scene.terrain.profiles)
    if not scene.platforms and not scene.stairs and not has_grade:return model
    if front_width_studs<=0:raise ValueError("front_width_studs must be positive")
    _validate_exterior_primitives(scene);main=scene.volumes[0];studs_per_meter=front_width_studs/main.width.value;plates_per_meter=studs_per_meter*COURSES_PER_STUD_RATIO*3;origin_x,origin_y,origin_z=_scene_bounds(scene);volume_x,volume_y,volume_z=_volume_bounds(scene);shift_x=_round_half_up((volume_x-origin_x)*studs_per_meter);shift_y=_round_half_up((volume_y-origin_y)*studs_per_meter);shift_z=_course_z(volume_z,origin_z,plates_per_meter)
    shifted=[part.model_copy(update={"x_studs":part.x_studs+shift_x,"y_studs":part.y_studs+shift_y,"z_plates":part.z_plates+shift_z}) for part in model.parts]
    extra=_terrain_parts(scene,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter)
    for platform in scene.platforms:extra.extend(_platform_parts(platform,scene,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter))
    for stair in scene.stairs:extra.extend(_stair_parts(stair,scene,origin_x=origin_x,origin_y=origin_y,origin_z=origin_z,studs_per_meter=studs_per_meter,plates_per_meter=plates_per_meter))
    all_parts=shifted+extra
    return model.model_copy(update={"width_studs":max(model.width_studs+shift_x,max(part.x_studs+1 for part in all_parts)),"depth_studs":max(model.depth_studs+shift_y,max(part.y_studs+1 for part in all_parts)),"height_plates":max(model.height_plates+shift_z,max(part.z_plates+3 for part in all_parts)),"parts":all_parts})
