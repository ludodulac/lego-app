# Spatial brick shell (BH-010)

BH-010 turns the four independent wall layouts from `BuildingBrickShell` into one globally positioned 3D shell.

## Global grid

The M0 global coordinate system is:

- `X` — front/rear span of the building;
- `Y` — left/right span (depth);
- `Z` — height in plate units.

Front and rear walls therefore run along X. Left and right walls run along Y.

## Corner ownership

A 1-stud-thick rectangular shell has four corner cells that belong geometrically to two adjacent walls. Two physical bricks cannot occupy the same cell.

BH-010 assigns each corner to one wall family per course:

- even courses: front/rear walls own the four corners;
- odd courses: left/right walls own the four corners.

The non-owning walls are re-tiled one stud short at both ends for that course. This avoids overlap and creates an alternating bond between perpendicular walls instead of four independent panels.

## Joint staggering

Because corner trimming can change a course composition, spatial generation re-tiles each facade course while carrying forward the previous course's internal joint positions. The BH-006 preference for avoiding vertically aligned joints therefore remains active after the 3D transition.

## Openings

Door/window cells already present in each wall grid remain blocked before re-tiling. The spatial shell does not fill these cells.

## Current limitations

BH-010 is deliberately limited to:

- one rectangular volume;
- one-stud-thick exterior walls;
- standard horizontal bricks from the M0 catalog;
- deterministic parity-based corner ownership.

It does not yet add a roof, floor/baseplate, lintel reinforcement, structural load analysis, special corner pieces, SNOT construction, or a global optimizer.

The output `SpatialBrickShell` is the first representation that can be rendered directly as a coherent 3D building shell.
