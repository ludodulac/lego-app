from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence
import math

Vec3 = tuple[float, float, float]
Mat4 = tuple[tuple[float, float, float, float], tuple[float, float, float, float], tuple[float, float, float, float], tuple[float, float, float, float]]
Triangle = tuple[Vec3, Vec3, Vec3]

EPS = 1e-7
CONTACT_EPS = 1e-5

class Relation(str, Enum):
    SEPARATED = "SEPARATED"
    CONTACT = "CONTACT"
    COLLISION = "COLLISION"

@dataclass(frozen=True)
class Transform:
    matrix: Mat4 = ((1.0,0.0,0.0,0.0),(0.0,1.0,0.0,0.0),(0.0,0.0,1.0,0.0),(0.0,0.0,0.0,1.0))

    @classmethod
    def translation(cls, x: float=0, y: float=0, z: float=0) -> "Transform":
        return cls(((1,0,0,x),(0,1,0,y),(0,0,1,z),(0,0,0,1)))

    def compose(self, other: "Transform") -> "Transform":
        a,b=self.matrix,other.matrix
        m=tuple(tuple(sum(a[r][k]*b[k][c] for k in range(4)) for c in range(4)) for r in range(4))
        return Transform(m)  # type: ignore[arg-type]

    def point(self, p: Vec3) -> Vec3:
        x,y,z=p;m=self.matrix
        return (m[0][0]*x+m[0][1]*y+m[0][2]*z+m[0][3], m[1][0]*x+m[1][1]*y+m[1][2]*z+m[1][3], m[2][0]*x+m[2][1]*y+m[2][2]*z+m[2][3])

@dataclass(frozen=True)
class AABB:
    minimum: Vec3
    maximum: Vec3
    def relation(self, other: "AABB", eps: float = CONTACT_EPS) -> Relation:
        touches=False
        for a0,a1,b0,b1 in zip(self.minimum,self.maximum,other.minimum,other.maximum):
            if a1 < b0-eps or b1 < a0-eps: return Relation.SEPARATED
            if abs(a1-b0)<=eps or abs(b1-a0)<=eps: touches=True
        return Relation.CONTACT if touches else Relation.COLLISION

@dataclass(frozen=True)
class Connector:
    type: str
    position: Vec3
    orientation: Vec3
    compatibility: tuple[str,...]
    tolerance: float
    owner_part: str | None = None

@dataclass(frozen=True)
class PartDefinition:
    part_id: str
    triangles: tuple[Triangle,...]
    bbox: AABB
    description: str = ""
    license: str = ""
    connectors: tuple[Connector,...] = ()

@dataclass(frozen=True)
class PartInstance:
    instance_id: str
    definition: PartDefinition
    transform: Transform = Transform()
    color: int | str | None = None
    @property
    def triangles(self) -> tuple[Triangle,...]:
        t=self.transform
        return tuple((t.point(a),t.point(b),t.point(c)) for a,b,c in self.definition.triangles)
    @property
    def bbox(self) -> AABB:
        pts=[p for tri in self.triangles for p in tri]
        return AABB(tuple(min(p[i] for p in pts) for i in range(3)), tuple(max(p[i] for p in pts) for i in range(3)))  # type: ignore[arg-type]

@dataclass
class AssemblyReport:
    valid: bool
    collisions: list[dict] = field(default_factory=list)
    contacts: list[dict] = field(default_factory=list)
    connections: list[dict] = field(default_factory=list)
    unsupported_parts: list[str] = field(default_factory=list)
    disconnected_components: list[list[str]] = field(default_factory=list)
    def to_dict(self): return asdict(self)

class LDrawLibrary:
    def __init__(self, root: str | Path, *, ignore_missing_primitives: bool=False):
        self.root=Path(root)
        self.ignore_missing_primitives=ignore_missing_primitives
        self._cache: dict[str,PartDefinition]={}

    def _resolve(self, name: str) -> Path | None:
        n=name.replace('\\','/').lower()
        if n.startswith('s/'):
            candidates=[self.root/'parts'/n]
        elif n.startswith('48/') or n.startswith('8/'):
            candidates=[self.root/'p'/n]
        else:
            candidates=[self.root/'parts'/n, self.root/'p'/n, self.root/'parts'/'s'/n]
        return next((p for p in candidates if p.exists()), None)

    def load_part(self, part_id: str) -> PartDefinition:
        key=part_id.lower().replace('\\','/')
        if not key.endswith('.dat'): key += '.dat'
        if key in self._cache: return self._cache[key]
        path=self._resolve(key)
        if not path: raise FileNotFoundError(f"LDraw part not found: {part_id}")
        description=""; license_line=""
        triangles=self._expand(path, Transform(), set())
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            if line.startswith('0 ') and not description and not line.startswith(('0 Name:','0 Author:','0 !')): description=line[2:].strip()
            if line.startswith('0 !LICENSE '): license_line=line[len('0 !LICENSE '):].strip()
        pts=[p for tri in triangles for p in tri]
        if not pts: raise ValueError(f"No surface triangles produced for {part_id}")
        bbox=AABB(tuple(min(p[i] for p in pts) for i in range(3)),tuple(max(p[i] for p in pts) for i in range(3)))  # type: ignore[arg-type]
        definition=PartDefinition(key, tuple(triangles), bbox, description, license_line, tuple(self._infer_basic_connectors(description,bbox)))
        self._cache[key]=definition
        return definition

    def _expand(self, path: Path, transform: Transform, stack: set[Path]) -> list[Triangle]:
        rp=path.resolve()
        if rp in stack: raise ValueError(f"Recursive LDraw reference: {path}")
        stack=stack|{rp}; out=[]; invert_next=False
        for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
            s=raw.strip()
            if not s: continue
            toks=s.split(); typ=toks[0]
            if typ=='0':
                if s.upper().startswith('0 BFC INVERTNEXT'): invert_next=True
                continue
            if typ=='1':
                if len(toks)<15: continue
                vals=list(map(float,toks[2:14])); name=' '.join(toks[14:])
                x,y,z,a,b,c,d,e,f,g,h,i=vals
                local=Transform(((a,b,c,x),(d,e,f,y),(g,h,i,z),(0,0,0,1)))
                ref=self._resolve(name)
                if ref is None:
                    if self.ignore_missing_primitives and path.parent.name.lower() in {'p','s'}: invert_next=False; continue
                    raise FileNotFoundError(f"Missing LDraw reference {name!r} from {path}")
                child=self._expand(ref, transform.compose(local), stack)
                if invert_next: child=[(t[0],t[2],t[1]) for t in child]
                out.extend(child); invert_next=False
            elif typ in {'3','4'}:
                nums=list(map(float,toks[2:]))
                pts=[transform.point((nums[i],nums[i+1],nums[i+2])) for i in range(0,len(nums),3)]
                if typ=='3' and len(pts)>=3: out.append((pts[0],pts[1],pts[2]))
                elif typ=='4' and len(pts)>=4:
                    out.append((pts[0],pts[1],pts[2])); out.append((pts[0],pts[2],pts[3]))
                invert_next=False
            else:
                invert_next=False
        return out

    def _infer_basic_connectors(self, description: str, bbox: AABB) -> Iterable[Connector]:
        import re
        m=re.search(r'\b(Brick|Plate)\s+(\d+)\s*x\s*(\d+)\b', description, re.I)
        if not m: return ()
        w,d=int(m.group(2)),int(m.group(3)); miny=bbox.minimum[1]; maxy=bbox.maximum[1]
        xs=[(j-(w-1)/2)*20 for j in range(w)]; zs=[(j-(d-1)/2)*20 for j in range(d)]
        con=[]
        for x in xs:
            for z in zs:
                con.append(Connector('stud',(x,miny,z),(0,-1,0),('anti_stud',),0.25))
                con.append(Connector('anti_stud',(x,maxy,z),(0,1,0),('stud',),0.25))
        return con

def instantiate(definition: PartDefinition, instance_id: str, transform: Transform | None=None, color=None) -> PartInstance:
    return PartInstance(instance_id, definition, transform or Transform(), color)

def _vsub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _norm(a): return math.sqrt(_dot(a,a))

def _segment_triangle(p0,p1,tri,eps=CONTACT_EPS):
    v0,v1,v2=tri; d=_vsub(p1,p0); e1=_vsub(v1,v0); e2=_vsub(v2,v0); h=_cross(d,e2); a=_dot(e1,h)
    if abs(a)<eps: return None
    f=1/a; s=_vsub(p0,v0); u=f*_dot(s,h)
    if u < -eps or u > 1+eps: return None
    q=_cross(s,e1); v=f*_dot(d,q)
    if v < -eps or u+v > 1+eps: return None
    t=f*_dot(e2,q)
    if not (-eps <= t <= 1+eps): return None
    return eps < t < 1-eps and u > eps and v > eps and u+v < 1-eps

def _coplanar(t1,t2,eps=CONTACT_EPS):
    n1=_cross(_vsub(t1[1],t1[0]),_vsub(t1[2],t1[0])); n2=_cross(_vsub(t2[1],t2[0]),_vsub(t2[2],t2[0]))
    l1,l2=_norm(n1),_norm(n2)
    if l1<eps or l2<eps: return False
    if _norm(_cross(n1,n2)) > eps*l1*l2: return False
    return abs(_dot(n1,_vsub(t2[0],t1[0]))) <= eps*l1

def _project2d(tri):
    n=_cross(_vsub(tri[1],tri[0]),_vsub(tri[2],tri[0])); drop=max(range(3),key=lambda i:abs(n[i]))
    return [tuple(p[i] for i in range(3) if i!=drop) for p in tri]

def _orient(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def _seg2(a,b,c,d,eps=CONTACT_EPS):
    o1,o2,o3,o4=_orient(a,b,c),_orient(a,b,d),_orient(c,d,a),_orient(c,d,b)
    return (o1*o2 <= eps and o3*o4 <= eps and max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0]))+eps and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1]))+eps)
def _point2(p,t,eps=CONTACT_EPS):
    o=[_orient(t[i],t[(i+1)%3],p) for i in range(3)]; return all(x>=-eps for x in o) or all(x<=eps for x in o)
def _coplanar_overlap(t1,t2):
    a,b=_project2d(t1),_project2d(t2)
    return any(_seg2(a[i],a[(i+1)%3],b[j],b[(j+1)%3]) for i in range(3) for j in range(3)) or _point2(a[0],b) or _point2(b[0],a)

def _tri_intersection_kind(t1,t2):
    if _coplanar(t1,t2): return Relation.CONTACT if _coplanar_overlap(t1,t2) else Relation.SEPARATED
    touched=False
    for tri,other in ((t1,t2),(t2,t1)):
        for i in range(3):
            hit=_segment_triangle(tri[i],tri[(i+1)%3],other)
            if hit is True: return Relation.COLLISION
            if hit is False: touched=True
    return Relation.CONTACT if touched else Relation.SEPARATED

def check_collision(a: PartInstance,b: PartInstance) -> Relation:
    if a.bbox.relation(b.bbox) is Relation.SEPARATED: return Relation.SEPARATED
    if a.triangles == b.triangles: return Relation.COLLISION
    saw_contact=False
    for ta in a.triangles:
        amin=tuple(min(p[i] for p in ta) for i in range(3)); amax=tuple(max(p[i] for p in ta) for i in range(3))
        for tb in b.triangles:
            bmin=tuple(min(p[i] for p in tb) for i in range(3)); bmax=tuple(max(p[i] for p in tb) for i in range(3))
            if any(amax[i] < bmin[i]-CONTACT_EPS or bmax[i] < amin[i]-CONTACT_EPS for i in range(3)): continue
            k=_tri_intersection_kind(ta,tb)
            if k is Relation.COLLISION: return k
            if k is Relation.CONTACT: saw_contact=True
    return Relation.CONTACT if saw_contact else Relation.SEPARATED

def find_contacts(a,b):
    return [{"part_a":a.instance_id,"part_b":b.instance_id,"type":"surface_contact"}] if check_collision(a,b) is Relation.CONTACT else []

def find_connections(a,b):
    out=[]
    for ca in a.definition.connectors:
        pa=a.transform.point(ca.position)
        for cb in b.definition.connectors:
            if cb.type not in ca.compatibility: continue
            pb=b.transform.point(cb.position)
            if _norm(_vsub(pa,pb)) <= max(ca.tolerance,cb.tolerance): out.append({"part_a":a.instance_id,"part_b":b.instance_id,"type":f"{ca.type}:{cb.type}","position":pa})
    return out

def analyze_assembly(parts: Sequence[PartInstance]) -> AssemblyReport:
    collisions=[]; contacts=[]; connections=[]; graph={p.instance_id:set() for p in parts}
    for i,a in enumerate(parts):
        for b in parts[i+1:]:
            rel=check_collision(a,b)
            if rel is Relation.COLLISION: collisions.append({"part_a":a.instance_id,"part_b":b.instance_id,"type":"solid_intersection"})
            elif rel is Relation.CONTACT:
                contacts.append({"part_a":a.instance_id,"part_b":b.instance_id,"type":"surface_contact"}); graph[a.instance_id].add(b.instance_id); graph[b.instance_id].add(a.instance_id)
            cs=find_connections(a,b); connections.extend(cs)
            if cs: graph[a.instance_id].add(b.instance_id); graph[b.instance_id].add(a.instance_id)
    if parts:
        base=max(p.bbox.maximum[1] for p in parts); roots={p.instance_id for p in parts if abs(p.bbox.maximum[1]-base)<=CONTACT_EPS}
    else: roots=set()
    supported=set(roots); frontier=list(roots)
    while frontier:
        n=frontier.pop()
        for m in graph[n]:
            if m not in supported: supported.add(m); frontier.append(m)
    unsupported=[p.instance_id for p in parts if p.instance_id not in supported]
    comps=[]; unseen=set(graph)
    while unseen:
        start=next(iter(unseen)); comp=set(); stack=[start]
        while stack:
            n=stack.pop()
            if n in comp: continue
            comp.add(n); unseen.discard(n); stack.extend(graph[n]-comp)
        comps.append(sorted(comp))
    return AssemblyReport(not collisions and not unsupported, collisions, contacts, connections, unsupported, sorted(comps))

def transform_from_ldraw(values: Sequence[float]) -> Transform:
    if len(values)!=12: raise ValueError("Expected x y z a b c d e f g h i")
    x,y,z,a,b,c,d,e,f,g,h,i=map(float,values)
    return Transform(((a,b,c,x),(d,e,f,y),(g,h,i,z),(0,0,0,1)))

def instance_from_dict(data: dict, library: LDrawLibrary) -> PartInstance:
    part_id=data.get('part_id') or data.get('part') or data.get('ldraw_id')
    if not part_id: raise ValueError("part_id is required")
    t=data.get('transform')
    if t is None:
        pos=data.get('position',[0,0,0]); tr=Transform.translation(*pos)
    elif isinstance(t,list) and len(t)==12: tr=transform_from_ldraw(t)
    elif isinstance(t,list) and len(t)==4: tr=Transform(tuple(tuple(map(float,row)) for row in t))  # type: ignore[arg-type]
    else: raise ValueError("transform must be 12 LDraw values or 4x4 matrix")
    return instantiate(library.load_part(str(part_id)), str(data.get('instance_id') or data.get('id') or part_id), tr, data.get('color'))
