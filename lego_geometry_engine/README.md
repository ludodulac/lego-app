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

## Coordinate and placement conventions

Canonical rectangular LDraw parts use local X for the longitudinal/second catalog dimension and local Z for the first/width dimension. BrickModel rotation `0` expects width on grid X and length on grid Y, so the standard BrickModel adapter applies the required base -90° rotation about LDraw Y before applying BrickModel quarter turns.

Official slope origins are not uniformly centered. Roof slopes are therefore bbox-anchored to the BrickModel footprint instead of using the standard centered transform. The adapter verifies the rotated LDraw bbox dimensions against the expected BrickModel footprint and preserves the requested `negative` / `positive` roof-side rise direction.

Window frames and their matching panes intentionally use the same BrickModel-to-LDraw assembly transform. Their real geometry is inset rather than represented as two coincident full boxes.

## Connectivity / support

Geometry and LEGO connectivity are separate. The milestone exposes a generic `Connector` and conservatively derives stud/anti-stud grids only for canonical `Brick W x D` / `Plate W x D` descriptions. Connector matching checks both position and opposing transformed orientation.

Connector grids follow the same official LDraw rectangular axes: the second/length dimension runs along local X and the first/width dimension along local Z. Connector vertical positions use nominal LEGO body mating planes rather than full mesh extrema, so the physical 4-LDU stud protrusion does not shift the logical stud/anti-stud connection plane.

Support is topological reachability through contact/connection edges from the lowest assembly elevation. This is not a stress or stability simulation.

## Data and licensing

Normal analysis is offline. Point `LDRAW_ROOT` at a local official LDraw Parts Library. The official library uses licenses declared in each part header; preserve attribution and license terms when redistributing files.

The regression fixture is deliberately small. The `3005` dependency closure includes official solid stud geometry so normal stacking is tested with the real stud protrusion. The `3037` slope and `60592` / `60601` window pair use reduced, attributed regression fixtures derived from official coordinates for the exact collision cases under test. See `tests/fixtures/ldraw/NOTICE.md` for details. **Production analysis must still use a complete official LDraw installation.**

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

Unknown canonical parts are never guessed. Strict mode raises `UnmappedCanonicalPartError`. Non-strict mode may analyze the mapped subset for diagnostics, but its result is explicitly `complete=False` and therefore `valid=False` while any placement is unmapped.

A regression test additionally enforces that every canonical part currently marked `PLACEMENT_APPROVED` by BrickHouse has a verified LDraw mapping. This prevents future catalog expansion from silently bypassing geometry validation.

## Current BrickHouse mapping coverage

### Standard M0 bricks

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

### Roof slopes and ridge tiles

| BrickHouse canonical ID | LDraw part |
| --- | --- |
| `BRICK_SLOPED_18_4X2` | `30363` |
| `BRICK_SLOPED_33_3X6` | `3939` |
| `BRICK_SLOPED_33_3X4` | `3297` |
| `BRICK_SLOPED_33_3X2` | `3298` |
| `BRICK_SLOPED_45_2X4` | `3037` |
| `BRICK_SLOPED_45_2X3` | `3038` |
| `BRICK_SLOPED_45_2X2` | `3039` |
| `BRICK_SLOPED_45_2X1` | `3040b` |
| `TILE_2X2` | `3068b` |
| `TILE_2X3` | `26603` |
| `TILE_2X4` | `87079` |

### Validated window assemblies

| BrickHouse canonical ID | LDraw part |
| --- | --- |
| `WINDOW_1X2X2_60592` | `60592` |
| `GLASS_FOR_WINDOW_1X2X2_60601` | `60601` |
| `WINDOW_1X2X3_60593` | `60593` |
| `GLASS_FOR_WINDOW_1X2X3_60602` | `60602` |
| `WINDOW_1X4X3_60594` | `60594` |
| `GLASS_FOR_WINDOW_1X4X3_60603` | `60603` |

The `60592` / `60601` regression uses official frame-opening and pane-envelope coordinates. The correctly co-located pair has no volumetric collision; moving the pane 1 LDU into the frame is detected as `COLLISION` and reported with both instance IDs.

## CLI

```bash
pip install -e ./lego_geometry_engine
lego-geometry analyze assembly.json --ldraw-root /path/to/ldraw
# or export LDRAW_ROOT=/path/to/ldraw
```

Each part needs `instance_id`, `part_id`, and either `position: [x,y,z]` in LDU, a 12-value LDraw transform (`x y z a b c d e f g h i`), or a 4x4 matrix.

## Milestone limits

This slice intentionally does not solve full Technic, clips, hinges, SNOT inference, mechanical stress/stability, MPD/TEXMAP coverage, or spatial indexing. Triangle narrow-phase remains correctness-first and pairwise after AABB culling; a spatial index can be added later without changing the public API.

The adapter is currently opt-in and is not automatically injected into the main BrickHouse generation/export pipeline. Production LDraw libraries must be complete—missing recursive references are errors.
