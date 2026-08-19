# Bill of Materials v0.1 (BH-013)

The BOM is generated only from the canonical `BrickModel`.

## Semantics

Each BOM line contains:

- canonical supplier-independent `part_id`;
- part category;
- integer quantity.

`total_parts` must equal the number of placements in the source BrickModel. `unique_part_types` is the number of BOM lines.

Lines are sorted deterministically by category then part id so serialization and later exports remain stable.

## Important boundary

The BOM does not yet contain vendor references, prices, colors, stock status or ordering links. Those are future mappings from canonical part ids to supplier-specific offers.

This separation is intentional: changing supplier must not change the geometric BrickModel or its canonical BOM.
