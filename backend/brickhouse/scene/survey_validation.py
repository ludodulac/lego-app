"""Cross-check an ArchitecturalScene against its validated ArchitecturalSurvey source."""
from __future__ import annotations
from collections import Counter
from enum import Enum
from math import dist
from pydantic import BaseModel
from brickhouse.building import Facade,OpeningType,RidgeDirection,RoofType
from brickhouse.survey import ArchitecturalSurvey,Certainty,ObservationKind,RelationKind
from .models import ArchitecturalScene,CONNECTIVITY_TOLERANCE_M,EdgeTreatment
class SceneSurveySeverity(str,Enum):WARNING="warning";ERROR="error"
class SceneSurveyIssue(BaseModel):code:str;severity:SceneSurveySeverity;message:str;object_id:str|None=None

def _semantic_opening_type(value):
    if value=="window":return OpeningType.WINDOW
    if value in {"door","door_or_glazed_door","glazed_door_or_large_glazed_opening"}:return OpeningType.DOOR
    if value=="garage_door":return OpeningType.GARAGE_DOOR
    return None
def _host_is_secondary(observation):return bool(observation.attributes.get("host_object"))
def _opening_threshold(scene,opening_id):
    o=next((i for i in scene.openings if i.id==opening_id),None)
    if o is None:return None
    v=next((i for i in scene.volumes if i.id==o.volume_id),None)
    if v is None:return None
    center=o.offset_horizontal+o.width/2;x0,y0,z0=v.position.x,v.position.y,v.position.z;x1=x0+v.width.value;y1=y0+v.depth.value;z=z0+o.offset_vertical
    if o.facade is Facade.FRONT:return x0+center,y0,z
    if o.facade is Facade.RIGHT:return x1,y0+center,z
    if o.facade is Facade.REAR:return x1-center,y1,z
    return x0,y1-center,z
def _point_on_platform(point,platform):
    x,y,z=point
    return platform.position.x-CONNECTIVITY_TOLERANCE_M<=x<=platform.position.x+platform.width+CONNECTIVITY_TOLERANCE_M and platform.position.y-CONNECTIVITY_TOLERANCE_M<=y<=platform.position.y+platform.depth+CONNECTIVITY_TOLERANCE_M and abs(z-platform.position.z)<=CONNECTIVITY_TOLERANCE_M
def _stair_touches_platform(stair,platform):return any(_point_on_platform((p.x,p.y,p.z),platform) for p in (stair.start,stair.end))
def _stair_touches_stair(a,b):
    aa=[(a.start.x,a.start.y,a.start.z),(a.end.x,a.end.y,a.end.z)];bb=[(b.start.x,b.start.y,b.start.z),(b.end.x,b.end.y,b.end.z)]
    return any(dist(x,y)<=CONNECTIVITY_TOLERANCE_M for x in aa for y in bb)
def _platform_touches_platform(a,b):
    if abs(a.position.z-b.position.z)>CONNECTIVITY_TOLERANCE_M:return False
    ax0,ax1=a.position.x,a.position.x+a.width;ay0,ay1=a.position.y,a.position.y+a.depth;bx0,bx1=b.position.x,b.position.x+b.width;by0,by1=b.position.y,b.position.y+b.depth
    x_gap=max(0.0,max(ax0,bx0)-min(ax1,bx1));y_gap=max(0.0,max(ay0,by0)-min(ay1,by1))
    return x_gap<=CONNECTIVITY_TOLERANCE_M and y_gap<=CONNECTIVITY_TOLERANCE_M

def _edge_access_interval(edge,offset):
    if edge.treatment in {EdgeTreatment.NONE,EdgeTreatment.ACCESS_OPENING,EdgeTreatment.UNKNOWN}:return (-float("inf"),float("inf"))
    if edge.treatment is EdgeTreatment.WALL_ATTACHED:return None
    for span in edge.access_spans:
        if span.from_offset-CONNECTIVITY_TOLERANCE_M<=offset<=span.to_offset+CONNECTIVITY_TOLERANCE_M:return span.from_offset,span.to_offset
    return None
def _interval_contains(container,required):
    if container is None:return False
    return required[0]>=container[0]-CONNECTIVITY_TOLERANCE_M and required[1]<=container[1]+CONNECTIVITY_TOLERANCE_M
def _edge_allows_interval(edge,required):
    if edge.treatment in {EdgeTreatment.NONE,EdgeTreatment.ACCESS_OPENING,EdgeTreatment.UNKNOWN}:return True
    if edge.treatment is EdgeTreatment.WALL_ATTACHED:return False
    return any(_interval_contains((s.from_offset,s.to_offset),required) for s in edge.access_spans)
def _stair_cross_interval(stair,edge_name,endpoint,platform):
    half=stair.width/2;x0,y0=platform.position.x,platform.position.y;dx=abs(stair.end.x-stair.start.x);dy=abs(stair.end.y-stair.start.y)
    if edge_name in {"y_min","y_max"}:
        center=endpoint.x-x0
        if dy>=dx:return center-half,center+half
        return center-CONNECTIVITY_TOLERANCE_M,center+CONNECTIVITY_TOLERANCE_M
    center=endpoint.y-y0
    if dx>=dy:return center-half,center+half
    return center-CONNECTIVITY_TOLERANCE_M,center+CONNECTIVITY_TOLERANCE_M
def _stair_platform_access_holds(stair,platform):
    if platform.edges is None:return True
    x0,x1=platform.position.x,platform.position.x+platform.width;y0,y1=platform.position.y,platform.position.y+platform.depth;checked=False
    for p in (stair.start,stair.end):
        if not _point_on_platform((p.x,p.y,p.z),platform):continue
        edges=[]
        if abs(p.x-x0)<=CONNECTIVITY_TOLERANCE_M:edges.append(("x_min",platform.edges.x_min,p.y-y0))
        if abs(p.x-x1)<=CONNECTIVITY_TOLERANCE_M:edges.append(("x_max",platform.edges.x_max,p.y-y0))
        if abs(p.y-y0)<=CONNECTIVITY_TOLERANCE_M:edges.append(("y_min",platform.edges.y_min,p.x-x0))
        if abs(p.y-y1)<=CONNECTIVITY_TOLERANCE_M:edges.append(("y_max",platform.edges.y_max,p.x-x0))
        if not edges:return True
        checked=True
        for name,edge,offset in edges:
            if _interval_contains(_edge_access_interval(edge,offset),_stair_cross_interval(stair,name,p,platform)):return True
    return not checked

def _platform_platform_access_holds(a,b):
    """Require protected shared edges to expose the whole real overlap between two connected platforms."""
    if a.edges is None and b.edges is None:return True
    ax0,ax1=a.position.x,a.position.x+a.width;ay0,ay1=a.position.y,a.position.y+a.depth;bx0,bx1=b.position.x,b.position.x+b.width;by0,by1=b.position.y,b.position.y+b.depth
    candidates=[]
    y0,y1=max(ay0,by0),min(ay1,by1)
    if y1>=y0-CONNECTIVITY_TOLERANCE_M:
        if abs(ax1-bx0)<=CONNECTIVITY_TOLERANCE_M:candidates.append(((a.edges.x_max if a.edges else None,(y0-ay0,y1-ay0)),(b.edges.x_min if b.edges else None,(y0-by0,y1-by0))))
        if abs(bx1-ax0)<=CONNECTIVITY_TOLERANCE_M:candidates.append(((a.edges.x_min if a.edges else None,(y0-ay0,y1-ay0)),(b.edges.x_max if b.edges else None,(y0-by0,y1-by0))))
    x0,x1=max(ax0,bx0),min(ax1,bx1)
    if x1>=x0-CONNECTIVITY_TOLERANCE_M:
        if abs(ay1-by0)<=CONNECTIVITY_TOLERANCE_M:candidates.append(((a.edges.y_max if a.edges else None,(x0-ax0,x1-ax0)),(b.edges.y_min if b.edges else None,(x0-bx0,x1-bx0))))
        if abs(by1-ay0)<=CONNECTIVITY_TOLERANCE_M:candidates.append(((a.edges.y_min if a.edges else None,(x0-ax0,x1-ax0)),(b.edges.y_max if b.edges else None,(x0-bx0,x1-bx0))))
    if not candidates:return True
    for pair in candidates:
        if all(edge is None or _edge_allows_interval(edge,required) for edge,required in pair):return True
    return False

def _certain_connection_holds(scene,subject_id,object_id):
    platforms={i.id:i for i in scene.platforms};stairs={i.id:i for i in scene.stairs};openings={i.id:i for i in scene.openings}
    if subject_id in stairs and object_id in platforms:return _stair_touches_platform(stairs[subject_id],platforms[object_id])
    if subject_id in platforms and object_id in stairs:return _stair_touches_platform(stairs[object_id],platforms[subject_id])
    if subject_id in stairs and object_id in stairs:return _stair_touches_stair(stairs[subject_id],stairs[object_id])
    if subject_id in platforms and object_id in platforms:return _platform_touches_platform(platforms[subject_id],platforms[object_id])
    if subject_id in openings and object_id in platforms:
        t=_opening_threshold(scene,subject_id);return t is not None and _point_on_platform(t,platforms[object_id])
    if subject_id in platforms and object_id in openings:
        t=_opening_threshold(scene,object_id);return t is not None and _point_on_platform(t,platforms[subject_id])
    return None

def _local_grade_elevation(scene,opening):
    if scene.terrain is None:return None
    profile=next((p for p in scene.terrain.profiles if p.facade is opening.facade),None)
    if profile is None:return None
    volume=next((v for v in scene.volumes if v.id==opening.volume_id),None)
    if volume is None:return None
    span=volume.width.value if opening.facade in {Facade.FRONT,Facade.REAR} else volume.depth.value
    if span<=0:return None
    center=min(max((opening.offset_horizontal+opening.width/2)/span,0.0),1.0)
    return profile.start_elevation+(profile.end_elevation-profile.start_elevation)*center

def validate_scene_against_survey(survey:ArchitecturalSurvey,scene:ArchitecturalScene)->list[SceneSurveyIssue]:
    issues=[];survey_openings={i.id:i for i in survey.observations if i.kind is ObservationKind.OPENING}
    front_width=next((i for i in survey.known_measurements if i.kind=="front_width"),None)
    if front_width is not None:
        main=scene.volumes[0] if scene.volumes else None
        if main is None or abs(main.width.value-front_width.value)>1e-6:issues.append(SceneSurveyIssue(code="front_width_measurement_drift",severity=SceneSurveySeverity.ERROR,object_id=main.id if main else None,message=f"La largeur avant mesurée dans le Survey vaut {front_width.value:g} m, mais la scène utilise {main.width.value if main else None!r}."))
        elif main.width.source.kind.value!="user_provided":issues.append(SceneSurveyIssue(code="front_width_provenance_drift",severity=SceneSurveySeverity.ERROR,object_id=main.id,message="La largeur avant utilisateur doit conserver source.kind='user_provided'."))
    for o in scene.openings:
        obs=survey_openings.get(o.id)
        if obs is None:issues.append(SceneSurveyIssue(code="scene_opening_not_in_survey",severity=SceneSurveySeverity.ERROR,object_id=o.id,message=f"L’ouverture {o.id!r} n’existe pas dans le Survey validé."));continue
        if obs.certainty is Certainty.UNPROVEN:issues.append(SceneSurveyIssue(code="unproven_opening_promoted",severity=SceneSurveySeverity.ERROR,object_id=o.id,message=f"L’ouverture {o.id!r} était non prouvée."))
        if obs.facade is not None and o.facade is not obs.facade:issues.append(SceneSurveyIssue(code="opening_facade_drift",severity=SceneSurveySeverity.ERROR,object_id=o.id,message=f"L’ouverture {o.id!r} a changé de façade."))
        expected=_semantic_opening_type(obs.attributes.get("semantic_type"))
        if expected is not None and o.type is not expected:issues.append(SceneSurveyIssue(code="opening_type_drift",severity=SceneSurveySeverity.ERROR,object_id=o.id,message=f"Le type de {o.id!r} ne respecte pas le Survey."))
        if o.local_grade_clearance is not None:
            grade=_local_grade_elevation(scene,o);volume=next((v for v in scene.volumes if v.id==o.volume_id),None)
            if grade is None or volume is None:issues.append(SceneSurveyIssue(code="local_grade_clearance_uncheckable",severity=SceneSurveySeverity.WARNING,object_id=o.id,message=f"L’ouverture {o.id!r} définit une garde au sol locale, mais aucun profil de terrain correspondant ne permet de la vérifier."))
            else:
                actual=volume.position.z+o.offset_vertical-grade
                if abs(actual-o.local_grade_clearance)>.20:issues.append(SceneSurveyIssue(code="local_grade_clearance_mismatch",severity=SceneSurveySeverity.ERROR,object_id=o.id,message=f"L’ouverture {o.id!r} annonce une garde au sol locale de {o.local_grade_clearance:g} m, mais sa géométrie et la pente donnent environ {actual:.2f} m."))
    scene_ids={i.id for i in scene.openings}
    for obs in survey_openings.values():
        if obs.certainty is Certainty.CERTAIN and obs.id not in scene_ids:issues.append(SceneSurveyIssue(code="certain_opening_missing",severity=SceneSurveySeverity.ERROR,object_id=obs.id,message=f"L’ouverture certaine {obs.id!r} a disparu de la Scene."))
    survey_counts=Counter(o.facade for o in survey_openings.values() if o.certainty is Certainty.CERTAIN and o.facade is not None and not _host_is_secondary(o));main_id=scene.volumes[0].id if scene.volumes else None;scene_counts=Counter(o.facade for o in scene.openings if o.volume_id==main_id);documented={p.facade for p in survey.photos}
    for facade in (Facade.FRONT,Facade.REAR,Facade.LEFT,Facade.RIGHT):
        if facade in documented and scene_counts.get(facade,0)!=survey_counts.get(facade,0):issues.append(SceneSurveyIssue(code="facade_opening_count_drift",severity=SceneSurveySeverity.ERROR,message=f"La façade {facade.value} doit conserver exactement {survey_counts.get(facade,0)} ouverture(s), la Scene en contient {scene_counts.get(facade,0)}."))
        elif facade not in documented and any(o.facade is facade for o in scene.openings):issues.append(SceneSurveyIssue(code="opening_on_undocumented_facade",severity=SceneSurveySeverity.ERROR,message=f"La Scene ajoute une ouverture sur la façade non documentée {facade.value}."))
    visibility={i.facade:i for i in scene.visibility}
    for o in scene.openings:
        entry=visibility.get(o.facade)
        if not entry:continue
        for span in entry.spans:
            if span.state.value!="visible" and o.offset_horizontal<span.to_offset and o.offset_horizontal+o.width>span.from_offset:issues.append(SceneSurveyIssue(code="opening_in_hidden_span",severity=SceneSurveySeverity.ERROR,object_id=o.id,message=f"L’ouverture {o.id!r} intersecte une zone {span.state.value}."));break
    certain_grade={i.facade for i in survey.observations if i.kind is ObservationKind.TERRAIN and i.certainty is Certainty.CERTAIN and i.facade is not None and i.attributes.get("slope_direction")};scene_grade={p.facade for p in (scene.terrain.profiles if scene.terrain else [])}
    for facade in certain_grade-scene_grade:issues.append(SceneSurveyIssue(code="certain_grade_missing",severity=SceneSurveySeverity.ERROR,message=f"La pente certaine sur {facade.value} a disparu."))
    front_gable=any(i.kind is ObservationKind.ROOF and i.certainty is Certainty.CERTAIN and i.facade is Facade.FRONT and i.attributes.get("front_is_gable") is True for i in survey.observations)
    if front_gable:
        roofs=[r for r in scene.roofs if r.type is RoofType.GABLE]
        if not roofs:issues.append(SceneSurveyIssue(code="front_gable_lost",severity=SceneSurveySeverity.ERROR,message="Le pignon avant certain a disparu."))
        elif any(r.ridge_direction is not RidgeDirection.DEPTH for r in roofs):issues.append(SceneSurveyIssue(code="front_gable_ridge_mismatch",severity=SceneSurveySeverity.ERROR,message="Un pignon avant impose ici ridge_direction=depth."))
    if any(i.kind is ObservationKind.CHIMNEY and i.certainty is Certainty.CERTAIN for i in survey.observations) and not scene.chimneys:issues.append(SceneSurveyIssue(code="certain_chimney_missing",severity=SceneSurveySeverity.ERROR,message="Une cheminée certaine a disparu."))
    ids_by_kind={ObservationKind.VOLUME:{i.id for i in scene.volumes},ObservationKind.PLATFORM:{i.id for i in scene.platforms},ObservationKind.STAIR:{i.id for i in scene.stairs}};codes={ObservationKind.VOLUME:"certain_volume_missing",ObservationKind.PLATFORM:"certain_platform_missing",ObservationKind.STAIR:"certain_stair_missing"}
    for obs in survey.observations:
        if obs.certainty is Certainty.CERTAIN and obs.kind in ids_by_kind and obs.id not in ids_by_kind[obs.kind]:issues.append(SceneSurveyIssue(code=codes[obs.kind],severity=SceneSurveySeverity.ERROR,object_id=obs.id,message=f"L’élément architectural certain {obs.id!r} a disparu ou changé d’id."))
    platforms={i.id:i for i in scene.platforms};stairs={i.id:i for i in scene.stairs}
    for relation in survey.relations:
        if relation.kind is not RelationKind.CONNECTS_TO or relation.certainty is not Certainty.CERTAIN:continue
        holds=_certain_connection_holds(scene,relation.subject_id,relation.object_id)
        if holds is False:issues.append(SceneSurveyIssue(code="certain_connection_broken",severity=SceneSurveySeverity.ERROR,object_id=relation.subject_id,message=f"La relation certaine {relation.id!r} n’est pas respectée géométriquement."));continue
        if holds is None:issues.append(SceneSurveyIssue(code="certain_connection_not_yet_checkable",severity=SceneSurveySeverity.WARNING,object_id=relation.subject_id,message=f"La relation certaine {relation.id!r} n’a pas encore de contrôle géométrique automatique."));continue
        stair=None;platform=None
        if relation.subject_id in stairs and relation.object_id in platforms:stair,platform=stairs[relation.subject_id],platforms[relation.object_id]
        elif relation.object_id in stairs and relation.subject_id in platforms:stair,platform=stairs[relation.object_id],platforms[relation.subject_id]
        if stair is not None and not _stair_platform_access_holds(stair,platform):issues.append(SceneSurveyIssue(code="certain_connection_blocked_by_platform_edge",severity=SceneSurveySeverity.ERROR,object_id=stair.id,message=f"La relation certaine {relation.id!r} ne dispose pas d’un passage assez large pour toute la volée. Élargis/corrige access_spans ou la géométrie de l’escalier."))
        if relation.subject_id in platforms and relation.object_id in platforms:
            a,b=platforms[relation.subject_id],platforms[relation.object_id]
            if not _platform_platform_access_holds(a,b):issues.append(SceneSurveyIssue(code="certain_platform_transition_blocked",severity=SceneSurveySeverity.ERROR,object_id=a.id,message=f"La relation certaine {relation.id!r} relie deux plateformes mais leur bord commun est bloqué par un garde-corps/muret continu ou un passage trop étroit."))
    return issues
