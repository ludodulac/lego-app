# M0 canonical brick catalog

BH-004 introduces the first supplier-independent catalog used by the deterministic engine.

## Principle

The engine works with canonical internal brick IDs, not with Rebrickable, LEGO, GoBricks, BrickLink, or supplier references.

Historical catalog data under `data/` remains useful for later mapping and enrichment, but it is not the runtime source of truth for M0 geometry.

## Grid units

Canonical standard bricks use integer construction-grid dimensions:

- `width_studs`: footprint width in studs;
- `length_studs`: footprint length in studs;
- `height_plates`: height in plate layers.

For M0, a normal brick has `height_plates = 3`.

This avoids introducing physical millimeter dimensions into the placement algorithm prematurely. A later conversion layer can map grid coordinates to render/physical dimensions.

## M0 catalog

The first catalog contains only 12 rectangular standard bricks:

- `BRICK_1X1`
- `BRICK_1X2`
- `BRICK_1X3`
- `BRICK_1X4`
- `BRICK_1X6`
- `BRICK_1X8`
- `BRICK_2X2`
- `BRICK_2X3`
- `BRICK_2X4`
- `BRICK_2X6`
- `BRICK_2X8`
- `BRICK_2X10`

These types are sufficient to begin wall tiling and bonding experiments.

## Rotation

Bricks may be rotated only by quarter turns in the horizontal plane for M0. A 90° or 270° rotation swaps width and length. Height is unchanged.

## Connections

All M0 catalog entries use the logical connection system `stud_tube`. Detailed connector coordinates are deliberately deferred until the placement/stability engine needs them.

## Out of scope for BH-004

- plates and tiles;
- slopes;
- windows and doors as specialized pieces;
- SNOT pieces;
- Technic connections;
- supplier references;
- availability, colors, pricing, stock;
- Rebrickable normalization;
- exact rendering mesh;
- brick placement.

## Relationship with historical data

`data/processed/piece_types_master.csv` already contains many of these IDs and was used as evidence that the selected basic types exist in the earlier catalog work. The canonical M0 catalog is intentionally much smaller and stricter.
