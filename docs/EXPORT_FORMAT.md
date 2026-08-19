# Brick export bundle (BH-014)

The export bundle is the stable file contract between the BrickHouse engine and downstream consumers such as the web viewer.

## Structure

```json
{
  "schema_version": "0.1",
  "building_id": "...",
  "volume_id": "...",
  "metadata": {
    "generator": "brickhouse-engine",
    "coordinate_system": "stud-grid",
    "vertical_unit": "plate"
  },
  "brick_model": { "...": "BrickModel v0.1" },
  "bom": { "...": "BillOfMaterials v0.1" }
}
```

The bundle validates that `building_id`, `volume_id` and total part count agree between the BrickModel and BOM.

## Coordinate semantics

- `x_studs`, `y_studs`: integer horizontal construction-grid coordinates.
- `z_plates`: integer vertical coordinate in plate units.
- `rotation_quarter_turns`: clockwise multiples of 90 degrees around the vertical axis.

## Determinism

`export_bundle_json()` serializes the validated Pydantic model directly, preserving the deterministic ordering already established by BrickModel and BOM generation.

## Downstream rule

Consumers must depend on this export contract rather than reconstructing geometry from `BuildingModel`. If the export schema changes incompatibly, increment `schema_version`.
