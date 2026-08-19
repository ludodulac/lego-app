# Gable roof generation — support-aware M0

BH-025 replaced the old floating-row roof approximation with an explicit support chain built from piece-family IDs already present in `data/processed/piece_types_master.csv`. BH-028 adds deterministic selection between the slope families whose support geometry is currently modeled by the engine.

## Modeled roof slope families

The processed source catalog contains many sloped-brick families (including 18°, 30°, 33°, 45°, 65° and others), but BrickHouse only treats a family as constructible after its rise/run and overlap rule have been modeled explicitly.

The current support registry includes:

### 33° family

- `BRICK_SLOPED_33_3X2`
- `BRICK_SLOPED_33_3X4`
- `BRICK_SLOPED_33_3X6`

Engine support abstraction:
- footprint depth across pitch: 3 studs;
- course advance: 2 studs;
- overlap: 1 stud row;
- rise: 3 plates per course.

### 45° family

- `BRICK_SLOPED_45_2X1`
- `BRICK_SLOPED_45_2X2`
- `BRICK_SLOPED_45_2X3`
- `BRICK_SLOPED_45_2X4`

Engine support abstraction:
- footprint depth across pitch: 2 studs;
- course advance: 1 stud;
- overlap: 1 stud row;
- rise: 3 plates per course.

The ridge bridge uses:

- `TILE_2X2`
- `TILE_2X3`
- `TILE_2X4`

These IDs already exist in the processed source catalog. They are not display-only `ROOF_TILE_*` placeholders.

## Pitch selection

BrickHouse computes the target pitch from the metric `RoofPlaneGeometry`, then selects the modeled family with the smallest absolute angular difference. Exact ties are resolved toward the lower pitch for deterministic output.

For example, the 35° reference house now selects the 33° family instead of blindly using 45°.

Families present in the CSV but not yet present in the support registry are intentionally ignored until their legal overlap/connection abstraction is implemented. This avoids claiming constructibility simply because a similarly named catalog part exists.

## Connection rule

The first course of each side starts at wall-top height and contacts the eave wall. Each later course advances inward by the selected family's exact course advance, overlaps the previous course, and rises by the selected family's exact connection rise.

At the center, a two-stud-wide ridge tile must overlap the innermost supported course of both roof sides.

`validate_roof_support()` rejects a roof when:

- an eave course is not anchored at the wall top;
- a later course does not follow the selected family's horizontal course advance;
- a later course has no overlap with the previous course;
- the vertical rise differs from the selected family's connection rise;
- the two sides use different slope families;
- the ridge does not overlap the innermost course of both roof sides.

The current M0 implementation still requires an even slope span. This avoids ambiguous center collisions until an odd-width ridge strategy is added.

## Design principle

The constructible piece family wins over arbitrary geometric deformation. BrickHouse approximates the photographed roof using the closest **modeled and supported** family rather than stretching a piece to force an exact visual pitch.

This deliberately prioritizes **physical connection consistency over perfect roof-pitch fidelity**.

## Remaining work

Future roof work includes adding support models for 18°, 30° and other useful catalog families, exact supplier-variant mapping, odd spans, roof overhangs, dormers, hips/valleys, chimneys, gutters, and richer connector geometry.
