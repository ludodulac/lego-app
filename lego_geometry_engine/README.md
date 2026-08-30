# LEGO Geometry & Assembly Engine

Autonomous local Python engine for geometric and topological validation of LEGO assemblies. It deliberately contains no Boldüngo architectural semantics.

## Public API

```python
from lego_geometry_engine import LDrawLibrary, Transform, instantiate, analyze_assembly

library = LDrawLibrary("/path/to/ldraw")
brick = library.load_part("3005")
parts = [
    instantiate(brick, "wall-1"),
    instantiate(brick, "wall-2", Transform.translation(0, -24, 0)),
]
report = analyze_assembly(parts)
print(report.to_dict())
```

Milestone surface: `LDrawLibrary.load_part`, `instantiate`, `check_collision`, `find_contacts`, `find_connections`, `analyze_assembly`, `Transform`, `PartDefinition`, `PartInstance`, `Connector`, `AssemblyReport`.

## Geometry

LDraw coordinates are retained internally: right-handed, `-Y` up; 20 LDU = one stud, 24 LDU = one brick height, 8 LDU = one plate. Type-1 matrices are recursively composed. Type-3 triangles and type-4 quads become collision triangles. Type-2 edges and type-5 conditional lines are non-solid and ignored.

Broad phase uses transformed AABBs only as a candidate filter. Narrow phase runs on transformed LDraw triangles and distinguishes `SEPARATED`, `CONTACT`, and `COLLISION`. For closed meshes, an additional ray-casting containment pass catches full enclosure even when no surface triangles cross. `CONTACT_EPS = 1e-5 LDU` and parser/collision epsilon `1e-7 LDU` are explicit in `core.py`.

`PartDefinition` is cached per `LDrawLibrary`; transformed triangles and AABBs are cached per immutable `PartInstance`.

## Connectivity / support

Geometry and LEGO connectivity are separate. The milestone exposes a generic `Connector` and conservatively derives stud/anti-stud grids only for canonical `Brick W x D` / `Plate W x D` descriptions. Connector matching checks both position and opposing transformed orientation. Support is topological reachability through contact/connection edges from the lowest assembly elevation. This is not a stress or stability simulation.

## Data and licensing

Normal analysis is offline. Point `LDRAW_ROOT` at a local official LDraw Parts Library. The official library uses licenses declared in each part header (legacy CC BY 2.0, newer CC BY 4.0, and some CC0); preserve attribution and license terms when redistributing files.

This repository includes only a tiny attributed regression fixture derived from official files `3005.dat`, `s/3005s01.dat`, `3037.dat`, `s/3037s01.dat`, `box4t.dat`, and `box5.dat`. It keeps exact polygon coordinates needed by the milestone collision regressions while omitting stud/cylindrical detail to keep the fixture small. **Production analysis must use a complete official LDraw installation.**

References: https://www.ldraw.org/article/218.html, https://www.ldraw.org/legal-info, https://library.ldraw.org/.

## Backend/runtime integration

The repository Docker image installs `./lego_geometry_engine` before the root BrickHouse package, so backend code can import the engine directly. The engine itself remains a Python library, not a microservice. Mapping BrickHouse canonical part IDs to real LDraw IDs intentionally stays in the application layer.

## CLI

```bash
pip install -e ./lego_geometry_engine
lego-geometry analyze assembly.json --ldraw-root /path/to/ldraw
# or export LDRAW_ROOT=/path/to/ldraw
```

Each part needs `instance_id`, `part_id`, and either `position: [x,y,z]` in LDU, a 12-value LDraw transform (`x y z a b c d e f g h i`), or a 4x4 matrix.

## Milestone limits

This slice intentionally does not solve Technic, clips, hinges, SNOT inference, mechanical stability, or catalogue-ID mapping. Triangle narrow-phase is correctness-first and pairwise after AABB culling; a spatial index can be added later without changing the public API. Production LDraw libraries must be complete—missing recursive references are errors.
