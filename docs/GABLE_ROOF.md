# Gable roof generation — support-aware M0

BH-025 replaces the old floating-row roof approximation with an explicit support chain built from piece-family IDs already present in `data/processed/piece_types_master.csv`.

## Roof pieces used by M0

Slope courses currently use:

- `BRICK_SLOPED_45_2X1`
- `BRICK_SLOPED_45_2X2`
- `BRICK_SLOPED_45_2X3`
- `BRICK_SLOPED_45_2X4`

The ridge bridge currently uses:

- `TILE_2X2`
- `TILE_2X3`
- `TILE_2X4`

These IDs already exist in the processed source catalog. They are not display-only `ROOF_TILE_*` placeholders.

## Connection rule

Each sloped brick is two studs deep across the roof pitch. A new course advances inward by one stud, so one stud row overlaps the preceding course in plan. Its bottom connection therefore lands on the high connection row of the previous course.

For the selected M0 45-degree family, each inward course rises by exactly one standard brick height (3 plates). The piece geometry dictates that rise; the engine no longer stretches or tilts a roof part to force an arbitrary metric Z value.

The first course of each side starts at wall-top height and contacts the eave wall. At the center, both sides terminate at adjacent high rows at the same elevation. A two-stud-wide tile bridge spans those two rows and acts as the ridge cap.

`validate_roof_support()` rejects a roof when:

- an eave course is not anchored at the wall top;
- a later course has no one-row overlap with the previous course;
- the vertical rise differs from the selected slope family's connection rise;
- the ridge does not overlap the innermost course of both roof sides.

The current M0 implementation also requires an even slope span. This avoids ambiguous center collisions until an odd-width ridge strategy is added.

## Relationship to the photographed roof pitch

The real metric roof geometry is still read and validated upstream, but M0 no longer deforms a 45-degree part to match that pitch. The constructible piece family wins. A later selector will choose the closest suitable family among the 18°, 25°, 30°, 33°, 45° and other sloped families already present in the source catalog.

That means this version prioritizes **physical connection consistency over exact roof-pitch fidelity**. This is deliberate: a slightly different but buildable roof is preferable to a visually accurate roof made of impossible floating parts.

## Remaining work

The support rule is still an engine-level approximation of legal stud/underside connections, not a complete supplier-exact connection graph. Future work includes exact variant mapping, richer connector geometry, automatic slope-family selection, odd spans, roof overhangs, dormers, hips/valleys, chimneys, gutters, and structural subassemblies where required.
