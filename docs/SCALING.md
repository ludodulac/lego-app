# Metric-to-brick scaling (BH-008)

BH-008 connects architectural geometry expressed in meters to the integer grid used by the brick-placement engine.

## Direction

The real building remains metric. We do not rewrite `BuildingModel` dimensions into toy dimensions. Instead, a model-size choice determines a scale for a wall, initially expressed as a target width in studs.

For a wall of width `W` meters and target width `S` studs:

`studs_per_meter = S / W`

Vertical scale preserves the physical proportion of the construction grid. A canonical stud pitch is 8 mm and a standard brick course (3 plates) is 9.6 mm, therefore:

`courses_per_meter = studs_per_meter / 1.2`

Wall height and opening boundaries are then quantized deterministically using half-up rounding.

## Openings

Door/window corners are projected onto the wall's local horizontal axis, so front, rear, left and right walls use the same scaling algorithm regardless of their world-space orientation.

After quantization, BH-007 validation is reused. Openings must remain inside the wall and may not overlap. If a feature becomes zero studs wide or zero courses high at the selected scale, scaling fails explicitly instead of silently deleting the feature.

## Current M0 limitation

The API currently chooses scale per wall using `target_width_studs`. This is the primitive needed to validate the bridge. The next building-level step must choose one shared scale for all walls of a building so adjacent facades remain dimensionally coherent.

Roof brickification, automatic scale recommendation, detail-aware scale selection and non-rectangular features are outside BH-008.
