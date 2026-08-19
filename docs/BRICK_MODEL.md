# BrickModel v0.1 (BH-012)

`BrickModel` is the canonical final placed-part representation for M0.

It sits after geometry, scaling, wall placement, corner bonding and roof generation:

`BuildingModel -> BuildingGeometry -> BuildingBrickShell -> SpatialBrickShell + SpatialRoof -> BrickModel`

## Purpose

Downstream systems should consume `BrickModel` rather than re-reading wall/roof implementation details. It is the intended contract for:

- 3D viewer;
- bill of materials;
- optimization/scoring;
- assembly-plan generation;
- later exports and instructions.

## Part record

Every `BrickModelPart` has:

- stable deterministic `placement_id`;
- canonical supplier-independent `part_id`;
- `category` (`brick`, `roof_tile`, `ridge_tile`);
- semantic `component` (`wall` or `roof`);
- global `x_studs`, `y_studs`, `z_plates`;
- quarter-turn rotation;
- wall `facade` or roof `roof_side` metadata.

The model preserves building/volume ids and its grid dimensions.

## Stable ids

M0 ids are sequential within deterministic source ordering:

- `wall-000001`, ...
- `roof-000001`, ...

They are placement ids, not supplier element numbers.

## Current limitations

Colors/materials, supplier mappings, price, availability, exact physical meshes, connection graphs and assembly dependencies are not yet part of BrickModel v0.1. These should be added as explicit later layers rather than inferred ad hoc by consumers.
