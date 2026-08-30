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

Geometry and LEGO connectivity are separate. The milestone exposes a generic `Connector` and conservatively derives stud/anti-stud grids only for canonical `Brick W x D` / `Plate W x D` descriptions. Connector matching checks both position and opposing transformed orientation. Connector positions use nominal LEGO mating planes rather than full mesh extrema, so a physical stud that protrudes 4 LDU above a brick does not shift the logical stud/anti-stud connection plane. Support is topological reachability through contact/connection edges from the lowest assembly elevation. This is not a stress or stability simulation.

## Data and licensing

Normal analysis is offline. Point `LDRAW_ROOT` at a local official LDraw Parts Library. The official library uses licenses declared in each part header (legacy CC BY 2.0, newer CC BY 4.0, and some CC0); preserve attribution and license terms when redistributing files.

The regression fixture is deliberately small. The `3005` dependency closure now includes the official solid stud geometry (`stud.dat` plus cylinder/disc primitives), so normal brick stacking is tested with the physical 4-LDU stud protrusion present. Non-solid edge/conditional drawing lines may be omitted because line types 2 and 5 are intentionally ignored by the collision loader. The `3037` regression remains a reduced slope shell containing the exact official polygon coordinates needed for the wall/slope tests. **Production analysis must still use a complete official LDraw installation.**

References: https://www.ldraw.org/article/218.html, https://www.ldraw.org/legal-info, https://library.ldraw.org/.

## Backend/runtime integration

The repository Docker image installs `./lego_geometry_engine` before the root BrickHouse package, so backend code can import the engine directly. The engine itself remains a Python library, not a microservice.

The application-layer bridge lives in `brickhouse.bricks.geometry_adapter`. It converts BrickModel grid coordinates (`x_studs`, `y_studs`, `z_plates`) into native LDraw coordinates and preserves each `placement_id` as the geometry-engine `instance_id`.

```python
from brickhouse.bricks.geometry_adapter import analyze_brick_model_geometry
from lego_geometry_engine import LDrawLibrary

library = LDrawLibrary("/path/to/ldraw")
result = analyze_brick_model_geometry(brick_model, library)
assert result.complete
print(result.report.to_dict())
```

The first verified mapping slice covers exactly the 12 standard M0 bricks:

| BrickHouse canonical ID | LDraw part |
| --- | --- |
| `BRICK_1X1` | `3005` |
| `BRICK_1X2` | `3004` |
| `BRICK_1X3` | `3622` |
| `BRICK_1X4` | `3010` |
| `BRICK_1X6` | `3009` |
| `BRICK_1X8` | `3008` |
| `BRICK_2X2` | `3003` |
| `BRICK_2X3` | `3002` |
| `BRICK_2X4` | `3001` |
| `BRICK_2X6` | `2456` |
| `BRICK_2X8` | `3007` |
| `BRICK_2X10` | `3006` |

Unknown canonical parts are never guessed. Strict mode raises `UnmappedCanonicalPartError`. Non-strict mode may analyze the mapped subset for diagnostics, but its result is explicitly `complete=False` and therefore `valid=False` while any placement is unmapped.

Roof slopes are deliberately not mapped by the generic brick transform yet. Official LDraw slope parts such as `3037` use part-specific origins, so correct integration requires verified anchor metadata per slope family rather than treating every footprint as a centered rectangular brick.

## CLI

```bash
pip install -e ./lego_geometry_engine
lego-geometry analyze assembly.json --ldraw-root /path/to/ldraw
# or export LDRAW_ROOT=/path/to/ldraw
```

Each part needs `instance_id`, `part_id`, and either `position: [x,y,z]` in LDU, a 12-value LDraw transform (`x y z a b c d e f g h i`), or a 4x4 matrix.

## Milestone limits

This slice intentionally does not solve Technic, clips, hinges, SNOT inference, mechanical stability, roof-slope anchor mapping, or a spatial index. Triangle narrow-phase is correctness-first and pairwise after AABB culling; a spatial index can be added later without changing the public API. Production LDraw libraries must be complete—missing recursive references are errors.
