# Gable roof generation — support-aware M0

The gable roof is no longer treated as a set of visually convenient floating rows. BH-025 introduces an explicit M0 support rule and maps the roof to piece-family IDs already present in `data/processed/piece_types_master.csv`.

## Roof pieces used by M0

Slope courses use the existing catalog family:

- `BRICK_SLOPED_45_2X1`
- `BRICK_SLOPED_45_2X2`
- `BRICK_SLOPED_45_2X3`
- `BRICK_SLOPED_45_2X4`

The ridge cap uses existing tile families:

- `TILE_1X1`
- `TILE_1X2`
- `TILE_1X4`

These are engine piece-family IDs already present in the processed source catalog. They are not invented display-only `ROOF_TILE_*` names.

## M0 connection rule

Each sloped course is two studs deep across the roof pitch. Courses advance inward by one stud at a time, so the new course overlaps the preceding course by one stud row in plan. That shared row represents the stud/underside connection used by the support validator.

The validator requires:

1. the first course of each roof side to start at wall-top height and contact its eave wall;
2. every later course to overlap the previous course;
3. no unsupported downward step and no vertical jump greater than the M0 connection limit;
4. the ridge cap to overlap the innermost course of both roof sides;
5. deterministic placement without duplicated center courses.

A roof that breaks these conditions raises an error instead of being exported as if it were constructible.

## Geometry

The metric rise/run from `BuildingGeometry` is still quantized onto the global stud/plate grid. The two-stud slope family provides the physical connection footprint while the Z sequence follows the target roof pitch as closely as the M0 grid allows.

## Current limitation

This is an important structural improvement, but it is not yet a full supplier-exact connection solver. The processed catalog tells us piece families, dimensions, availability counts and colors; it does not yet encode every underside tube, stud, hinge or legal connection surface for every variant. A later catalog layer will map the chosen engine family to exact purchasable variants and richer connection geometry.

Other later work includes roof overhangs, dormers, hips/valleys, chimneys, gutters, and automated selection among 18°, 25°, 30°, 33°, 45° and other slope families already present in the source data.
