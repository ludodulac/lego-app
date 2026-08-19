# Building brick shell (BH-009)

BH-009 is the first building-level brick representation. It takes the four metric wall surfaces of one rectangular volume and generates four brick wall layouts using one shared model scale.

## Scale rule

The front facade is the M0 reference. If its metric width is `W` meters and the requested model width is `S` studs:

`studs_per_meter = S / W`

That value is then reused unchanged for front, rear, left and right walls. Side-wall widths are rounded half-up only after applying the shared scale.

Example: a 10 m x 8 m building at 48 studs on the front uses 4.8 studs/m. Front and rear become 48 studs; left and right become 38 studs (`8 x 4.8 = 38.4`, rounded half-up).

Vertical scale is shared as well using the canonical brick proportions introduced in BH-008, so all four walls have one coherent number of brick courses.

## Output

`BuildingBrickShell` stores:

- building and volume IDs;
- reference facade and target width;
- shared studs-per-meter scale;
- exactly four `BuildingWallLayout` records;
- for each wall, its `WallGridSpec` and its opening-aware `WallBrickLayout`.

The facade order is deterministic: front, rear, left, right.

## Validation

M0 accepts only one rectangular four-wall shell. It rejects missing/duplicate facades, multiple volume IDs, unequal opposite-wall dimensions, unequal wall heights, collapsed openings, and other invalid grid conditions inherited from BH-007/BH-008.

## Current limitation

The four wall layouts are dimensionally coherent but are not yet physically interlocked at the corners. BH-009 therefore represents a complete *digital wall shell*, not yet a structurally bonded 3D building. Corner bonding and world-space brick placement are the next layer.

Roof brickification is also outside BH-009.
