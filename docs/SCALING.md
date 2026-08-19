# Metric-to-brick scaling (BH-008)

BH-008 connects architectural geometry expressed in meters to the integer grid used by the brick-placement engine.

## Direction

The real building remains metric. We do not rewrite `BuildingModel` dimensions into toy dimensions. Instead, a model-size choice determines a scale for a wall, initially expressed as a target width in studs.

For a wall of width `W` meters and target width `S` studs:

`studs_per_meter = S / W`

Vertical scale preserves the physical proportion of the construction grid. A canonical stud pitch is 8 mm and a standard brick course (3 plates) is 9.6 mm, therefore:

`courses_per_meter = studs_per_meter / 1.2`

Wall height and opening boundaries are quantized deterministically using half-up rounding.

Example: a 10 m wall mapped to 48 studs has `4.8 studs/m`. A 5.6 m wall height becomes about 22 standard brick courses. This is intentionally not 27 courses: horizontal and vertical toy dimensions are different, and the engine preserves that physical proportion instead of stretching the model.

## Openings

Door/window corners are projected onto the wall's local horizontal axis, so front, rear, left and right walls use the same scaling algorithm regardless of their world-space orientation.

After quantization, BH-007 validation is reused. Openings must remain inside the wall and may not overlap. If a feature becomes zero studs wide or zero courses high at the selected scale, scaling fails explicitly instead of silently deleting the feature. Later product logic may use this signal to recommend a more detailed model size or simplify the feature deliberately.

## Public API

- `discretize_wall_geometry(wall, target_width_studs) -> WallGridSpec`
- `generate_scaled_wall_layout(wall, target_width_studs) -> WallBrickLayout`

The second helper is the first direct bridge from metric architectural geometry to an actual brick placement result.

## Current M0 limitation

The API currently chooses scale per wall using `target_width_studs`. This validates the metric-to-grid bridge but is not yet sufficient for assembling a complete building: all walls of one building must share one global scale so connected dimensions agree.

That building-level shared scale is the next architectural step before assembling four walls.

Roof brickification, automatic scale recommendation, detail-aware scale selection, color mapping and non-rectangular features are outside BH-008.
