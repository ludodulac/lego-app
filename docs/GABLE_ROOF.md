# Gable roof generation (BH-011)

BH-011 adds the first roof that can be generated above the M0 spatial brick shell.

## Goal

Turn the two metric gable roof planes already present in `BuildingGeometry` into a deterministic stepped roof on the same global X/Y/Z brick grid as the walls.

## Canonical roof parts

The roof generator is supplier-independent. M0 introduces a deliberately small roof catalog:

- `ROOF_TILE_1X1`, `1X2`, `1X4`, `1X6`, `1X8`
- `RIDGE_TILE_1X1`, `1X2`, `1X4`, `1X6`, `1X8`

These IDs describe engine-level functional pieces, not LEGO/Rebrickable/vendor references. Mapping to real purchasable elements belongs to a later catalog layer.

## Geometry

The roof uses the metric rise/run ratio of the `RoofPlaneGeometry` produced by the geometry engine. The ratio is converted into the brick grid using the physical grid proportion already established by BH-008:

- horizontal: studs
- vertical: plates
- 1 horizontal stud corresponds proportionally to 2.5 vertical plates before applying roof slope.

Each grid coordinate across the roof slope receives one horizontal roof row. Its Z position is quantized deterministically with half-up rounding. Rows nearer the ridge are higher than rows at the eaves.

The generator supports both existing ridge directions:

- `depth`: slope changes along X and roof rows run along Y;
- `width`: slope changes along Y and roof rows run along X.

A final canonical ridge row is placed one plate above the highest central stepped row.

## Current M0 limitations

This is intentionally a stepped approximation, not yet a final photorealistic or vendor-exact roof solution.

Not yet implemented:

- mapping the abstract roof tiles to exact slope-piece geometries;
- roof overhang projection beyond the wall footprint in the brick shell;
- flat roofs;
- dormers;
- hip/valley roofs;
- chimneys and roof penetrations;
- gutters and fascia;
- structural roof supports/trusses;
- optimized slope selection based on real available parts.

Those features can be added without changing the upstream `BuildingModel -> BuildingGeometry` contract.
